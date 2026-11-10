"""Local-only HTTP endpoints for deterministic stream checker tests."""

import threading
import time
from collections import Counter
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


TS_BYTES = (b'\x47' + b'\x00' * 187) * 100


def playlist(target):
    return (
        '#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:5\n'
        f'#EXTINF:5.0,\n{target}\n'
    ).encode()


class FixtureHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def log_message(self, format, *args):
        pass

    def send_data(self, status, body=b'', content_type='text/plain', headers=None):
        try:
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        path = urlsplit(self.path).path
        with self.server.lock:
            self.server.hits[path] += 1
            count = self.server.hits[path]
        if path in ('/valid.m3u8', '/flaky.m3u8'):
            if path == '/flaky.m3u8' and count == 1:
                self.send_data(503, b'temporary failure')
            else:
                self.send_data(200, playlist('segment.ts'), 'application/vnd.apple.mpegurl')
        elif path == '/master.m3u8':
            body = b'#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=100000\n/redirect\n'
            self.send_data(200, body, 'application/vnd.apple.mpegurl')
        elif path == '/alternate-master.m3u8':
            body = (b'#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1\n/no-variant.m3u8\n'
                    b'#EXT-X-STREAM-INF:BANDWIDTH=2\n/valid.m3u8\n')
            self.send_data(200, body, 'application/vnd.apple.mpegurl')
        elif path == '/redirect':
            self.send_data(302, headers={'Location': '/nested/redirected.m3u8'})
        elif path == '/nested/redirected.m3u8':
            self.send_data(200, playlist('segments/media.ts'), 'application/vnd.apple.mpegurl')
        elif path in ('/segment.ts', '/nested/segments/media.ts', '/raw', '/media2'):
            self.send_data(200, TS_BYTES, 'video/mp2t')
        elif path == '/missing.m3u8':
            self.send_data(200, playlist('/does-not-exist.ts'), 'application/vnd.apple.mpegurl')
        elif path == '/html-segment.m3u8':
            self.send_data(200, playlist('/html'), 'application/vnd.apple.mpegurl')
        elif path == '/html':
            self.send_data(200, b'<html>#EXTM3U\n#EXTINF:5,\nfoo.ts</html>' * 20, 'text/html')
        elif path == '/empty.m3u8':
            self.send_data(200, b'#EXTM3U\n#EXT-X-TARGETDURATION:5\n', 'application/vnd.apple.mpegurl')
        elif path == '/malformed.m3u8':
            self.send_data(200, playlist('http://[broken'), 'application/vnd.apple.mpegurl')
        elif path == '/control-char.m3u8':
            self.send_data(200, playlist('/invalid\x00segment'), 'application/vnd.apple.mpegurl')
        elif path == '/bom.m3u8':
            self.send_data(200, b'\xef\xbb\xbf\n' + playlist('segment.ts'), 'application/vnd.apple.mpegurl')
        elif path == '/forbidden':
            self.send_data(403, playlist('segment.ts'), 'application/vnd.apple.mpegurl')
        elif path == '/slow':
            time.sleep(1)
            self.send_data(200, TS_BYTES, 'video/mp2t')
        elif path == '/slow-manifest.m3u8':
            time.sleep(0.25)
            self.send_data(200, playlist('/slow-segment.ts'), 'application/vnd.apple.mpegurl')
        elif path == '/slow-segment.ts':
            time.sleep(0.5)
            self.send_data(200, TS_BYTES, 'video/mp2t')
        elif path == '/infinite':
            try:
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp2t')
                self.end_headers()
                for _ in range(2000):
                    self.wfile.write(TS_BYTES[:752])
                    self.wfile.flush()
                    time.sleep(0.002)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_data(404, b'Not found')


@contextmanager
def fixture_server():
    server = ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
    server.daemon_threads = True
    server.lock = threading.Lock()
    server.hits = Counter()
    server.base_url = f'http://127.0.0.1:{server.server_port}'
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
