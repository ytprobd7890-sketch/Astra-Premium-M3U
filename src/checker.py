"""Bounded, parallel checks for HTTP(S) HLS playlists and media streams."""

import os
import re
import selectors
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlsplit


# A small prefix is enough to recognize a playlist or media without downloading
# an entire segment (or an endless MPEG-TS stream).
_READ_LIMIT = 16 * 1024
_MAX_PLAYLIST_DEPTH = 4


def _response_headers(path, original_url):
    """Return the last HTTP status/headers and resolve any followed redirects."""
    if not path.exists():
        return 0, {}, original_url

    raw = path.read_text(encoding="iso-8859-1", errors="replace")
    status, headers, effective_url = 0, {}, original_url
    for block in re.split(r"\r?\n\r?\n", raw):
        lines = block.splitlines()
        if not lines:
            continue
        match = re.match(r"^HTTP/\S+\s+(\d{3})", lines[0], re.IGNORECASE)
        if not match:
            continue
        status = int(match.group(1))
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        if 300 <= status < 400 and headers.get("location"):
            try:
                effective_url = urljoin(effective_url, headers["location"])
            except ValueError:
                # A malformed redirect is a failed stream, not a reason to
                # abort the entire playlist check.
                pass
    return status, headers, effective_url


def _fetch_prefix(url, timeout, proxy=None):
    """Fetch at most _READ_LIMIT bytes, stopping even if a stream never ends.

    curl enforces a request timeout, and the selector also enforces a deadline
    while reading its output. Redirects are limited to HTTP(S). A configured
    proxy is always used for the proxy attempt; a direct attempt ignores any
    proxy variables inherited from the runner.
    """
    with tempfile.TemporaryDirectory(prefix="astra-check-") as directory:
        header_path = Path(directory) / "headers"
        cmd = [
            "curl", "-q", "--silent", "--show-error", "--location",
            "--max-redirs", "5", "--proto", "=http,https",
            "--proto-redir", "=http,https", "--compressed",
            "--max-time", f"{timeout:.3f}",
            "--connect-timeout", f"{min(timeout, 5):.3f}",
            "--dump-header", str(header_path),
        ]
        if proxy:
            cmd.extend(["--proxy", proxy, "--noproxy", ""])
        else:
            cmd.extend(["--proxy", ""])
        cmd.extend(["--", url])

        deadline = time.monotonic() + timeout
        body = bytearray()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while len(body) < _READ_LIMIT:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        break
                    chunk = os.read(process.stdout.fileno(), _READ_LIMIT - len(body))
                    if not chunk:
                        break
                    body.extend(chunk)
        finally:
            # A raw live stream may never finish on its own. The prefix is all
            # we need, so stop curl and always reap it before removing temp files.
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=0.25)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            process.stdout.close()

        status, headers, effective_url = _response_headers(header_path, url)
        return {
            "http_code": status,
            "headers": headers,
            "url": effective_url,
            "body": bytes(body),
            "truncated": len(body) == _READ_LIMIT,
        }


def _playlist_targets(body, base_url, truncated=False):
    """Find HLS variants or media segments, resolving relative URLs."""
    text = body.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    if truncated and text and not text.endswith(("\n", "\r")):
        lines = lines[:-1]  # The last URI may have been cut off at the limit.
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines or lines[0].strip() != "#EXTM3U":
        return []

    variants, segments = [], []

    def add_target(destination, reference):
        if any(ord(char) < 32 or ord(char) == 127 for char in reference):
            return
        try:
            target = urljoin(base_url, reference)
            parsed = urlsplit(target)
            has_control_chars = any(ord(char) < 32 or ord(char) == 127 for char in target)
            if parsed.scheme.lower() in ("http", "https") and parsed.netloc and not has_control_chars:
                destination.append(target)
        except ValueError:
            pass  # Invalid child URLs must not abort checks for other streams.

    pending = None
    for raw_line in lines[1:]:
        line = raw_line.strip()
        upper = line.upper()
        if upper.startswith("#EXT-X-STREAM-INF:"):
            pending = variants
        elif upper.startswith("#EXTINF:"):
            pending = segments
        elif upper.startswith("#EXT-X-PART:"):
            # Low-latency HLS can advertise parts before a full segment.
            match = re.search(r'(?:^|,)\s*URI="([^"]+)"', line.split(":", 1)[1], re.IGNORECASE)
            if match:
                add_target(segments, match.group(1))
        elif line and not line.startswith("#") and pending is not None:
            add_target(pending, line)
            pending = None

    # Try a few alternate variants if one is unavailable. For live media, the
    # most recent complete segments are usually the least likely to be expired.
    return variants[:3] if variants else list(reversed(segments[-2:]))


def _looks_like_media(body, content_type):
    """Recognize a media prefix, rejecting common HTML/JSON error pages."""
    if len(body) < 188:
        return False
    prefix = body[:512].lstrip().lower()
    if prefix.startswith((b"<", b"{", b"[")) or b"<html" in prefix:
        return False

    # MPEG-TS can begin partway through a packet. Look for three sync bytes.
    for offset in range(min(188, max(0, len(body) - 376))):
        if body[offset] == body[offset + 188] == body[offset + 376] == 0x47:
            return True

    mime = content_type.split(";", 1)[0].strip().lower()
    if mime.startswith(("video/", "audio/")):
        return True
    if body[4:8] in (b"ftyp", b"styp", b"moof"):
        return True  # MP4/fMP4, including HLS fragments.
    if mime in ("application/octet-stream", "binary/octet-stream"):
        sample = body[:512]
        return b"\x00" in sample or sum(byte >= 128 for byte in sample) > len(sample) // 5
    return False


def _probe_once(url, timeout, proxy, deep_check):
    """Check one URL, sharing one timeout across redirects and HLS children."""
    start = time.monotonic()
    deadline = start + timeout
    root_status = root_size = 0
    error = "No playable media found"
    pending = [(url, 0)]
    visited = set()

    while pending:
        target, depth = pending.pop()
        if target in visited or depth > _MAX_PLAYLIST_DEPTH:
            continue
        visited.add(target)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            error = "Check timed out"
            break
        if urlsplit(target).scheme.lower() not in ("http", "https"):
            error = "Only HTTP(S) streams are supported"
            continue

        response = _fetch_prefix(target, remaining, proxy)
        status, body = response["http_code"], response["body"]
        if depth == 0:
            root_status, root_size = status, len(body)
        if status not in (200, 206):
            error = f"HTTP {status}" if status else "Connection failed or timed out"
            continue

        if body.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"#EXTM3U"):
            targets = _playlist_targets(body, response["url"], response["truncated"])
            if not targets:
                error = "HLS playlist has no playable entries"
                continue
            if not deep_check:
                return {
                    "url": url, "is_live": True, "http_code": root_status,
                    "size": root_size, "latency_ms": int((time.monotonic() - start) * 1000),
                    "error": None,
                }
            if depth == _MAX_PLAYLIST_DEPTH:
                error = "HLS playlist nesting limit exceeded"
                continue
            pending.extend((child, depth + 1) for child in reversed(targets))
        elif _looks_like_media(body, response["headers"].get("content-type", "")):
            return {
                "url": url, "is_live": True, "http_code": root_status,
                "size": root_size, "latency_ms": int((time.monotonic() - start) * 1000),
                "error": None,
            }
        else:
            error = "Response is not recognizable media"

    return {
        "url": url, "is_live": False, "http_code": root_status,
        "size": root_size, "latency_ms": int((time.monotonic() - start) * 1000),
        "error": error,
    }


def check_url(url, timeout=8, proxy=None, retries=1, deep_check=False):
    """Check one stream, retrying failed responses as well as connection errors."""
    if timeout <= 0 or retries < 0:
        raise ValueError("timeout must be positive and retries must be non-negative")
    for attempt in range(retries + 1):
        result = _probe_once(url, timeout, proxy, deep_check)
        if result["is_live"]:
            return result
        if attempt < retries:
            time.sleep(0.2)
    return result


def check_urls_parallel(urls, timeout=8, workers=50, proxy=None, retries=1,
                        use_proxy_fallback=True, deep_check=False):
    """Check every URL in parallel, including any direct proxy fallback.

    Results are returned in input order. Each direct fallback gets one attempt;
    proxy attempts get the configured number of retries.
    """
    if workers < 1:
        raise ValueError("workers must be positive")
    if not shutil.which("curl"):
        raise RuntimeError("curl is required to check streams")

    def check_with_fallback(url):
        result = check_url(url, timeout, proxy, retries, deep_check)
        if proxy and use_proxy_fallback and not result["is_live"]:
            direct = check_url(url, timeout, None, 0, deep_check)
            if direct["is_live"]:
                direct["via"] = "direct_fallback"
                return direct
            result["via"] = "proxy_failed"
        else:
            result["via"] = "proxy" if proxy else "direct"
        return result

    results = [None] * len(urls)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(check_with_fallback, url): index for index, url in enumerate(urls)}
        for completed, future in enumerate(as_completed(futures), start=1):
            results[futures[future]] = future.result()
            if completed % 250 == 0 or completed == len(urls):
                print(f"Checked {completed}/{len(urls)} URLs", flush=True)
    return results
