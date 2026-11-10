import os
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import checker
from http_fixtures import fixture_server


class StreamCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server_context = fixture_server()
        cls.server = cls.server_context.__enter__()
        cls.base = cls.server.base_url

    @classmethod
    def tearDownClass(cls):
        cls.server_context.__exit__(None, None, None)

    def setUp(self):
        with self.server.lock:
            self.server.hits.clear()

    def check(self, path, **kwargs):
        return checker.check_url(self.base + path, timeout=2, retries=0, **kwargs)

    def test_hls_segment_and_direct_mpeg_ts_are_live(self):
        for path in ('/valid.m3u8', '/raw'):
            with self.subTest(path=path):
                result = self.check(path, deep_check=True)
                self.assertTrue(result['is_live'], result)
                self.assertEqual(result['http_code'], 200)
                self.assertGreater(result['size'], 0)
        self.assertEqual(self.server.hits['/segment.ts'], 1)

    def test_master_redirect_and_relative_segment_are_followed(self):
        result = self.check('/master.m3u8', deep_check=True)
        self.assertTrue(result['is_live'], result)
        self.assertEqual(self.server.hits['/nested/segments/media.ts'], 1)

    def test_alternate_variant_is_tried(self):
        result = self.check('/alternate-master.m3u8', deep_check=True)
        self.assertTrue(result['is_live'], result)
        self.assertEqual(self.server.hits['/no-variant.m3u8'], 1)
        self.assertEqual(self.server.hits['/valid.m3u8'], 1)

    def test_deep_check_rejects_missing_or_html_media(self):
        for path in ('/missing.m3u8', '/html-segment.m3u8'):
            with self.subTest(path=path):
                self.assertFalse(self.check(path, deep_check=True)['is_live'])
        self.assertTrue(self.check('/missing.m3u8', deep_check=False)['is_live'])

    def test_invalid_responses_are_not_live(self):
        for path in ('/html', '/empty.m3u8', '/forbidden', '/does-not-exist'):
            with self.subTest(path=path):
                self.assertFalse(self.check(path, deep_check=True)['is_live'])
        self.assertEqual(self.check('/forbidden')['http_code'], 403)

    def test_malformed_child_does_not_abort_other_checks(self):
        urls = [self.base + '/malformed.m3u8', self.base + '/control-char.m3u8', self.base + '/valid.m3u8']
        results = checker.check_urls_parallel(urls, timeout=2, workers=3, retries=0, deep_check=True)
        self.assertEqual([result['is_live'] for result in results], [False, False, True])

    def test_playlist_with_bom_and_leading_blank_line(self):
        self.assertTrue(self.check('/bom.m3u8', deep_check=True)['is_live'])

    def test_http_failures_are_retried(self):
        result = checker.check_url(self.base + '/flaky.m3u8', timeout=2, retries=1, deep_check=True)
        self.assertTrue(result['is_live'], result)
        self.assertEqual(self.server.hits['/flaky.m3u8'], 2)

    def test_proxy_failure_falls_back_direct_even_when_no_proxy_is_set(self):
        with patch.dict(os.environ, {'NO_PROXY': '127.0.0.1', 'no_proxy': '127.0.0.1'}):
            result = checker.check_urls_parallel(
                [self.base + '/valid.m3u8'], timeout=1, workers=1,
                proxy='http://127.0.0.1:1', retries=0, deep_check=True,
            )[0]
        self.assertTrue(result['is_live'], result)
        self.assertEqual(result['via'], 'direct_fallback')

    def test_endless_stream_is_sampled_without_waiting_for_timeout(self):
        started = time.monotonic()
        result = checker.check_url(self.base + '/infinite', timeout=4, retries=0, deep_check=True)
        self.assertTrue(result['is_live'], result)
        self.assertLess(time.monotonic() - started, 3)
        self.assertLessEqual(result['size'], checker._READ_LIMIT)

    def test_slow_response_respects_the_attempt_timeout(self):
        started = time.monotonic()
        result = checker.check_url(self.base + '/slow', timeout=0.2, retries=0, deep_check=True)
        self.assertFalse(result['is_live'])
        self.assertLess(time.monotonic() - started, 2)

    def test_hls_manifest_and_segment_share_one_timeout(self):
        started = time.monotonic()
        result = checker.check_url(self.base + '/slow-manifest.m3u8', timeout=0.4, retries=0, deep_check=True)
        self.assertFalse(result['is_live'])
        self.assertLess(time.monotonic() - started, 2)

    def test_fallbacks_are_parallel_and_results_keep_input_order(self):
        barrier = threading.Barrier(3, timeout=3)
        direct_calls = []
        lock = threading.Lock()

        def fake_check(url, timeout, proxy, retries, deep_check):
            if proxy:
                return {'url': url, 'is_live': False}
            with lock:
                direct_calls.append(url)
            barrier.wait()
            return {'url': url, 'is_live': True}

        urls = ['http://example.test/one', 'http://example.test/two', 'http://example.test/three']
        with patch.object(checker, 'check_url', side_effect=fake_check):
            results = checker.check_urls_parallel(urls, workers=3, proxy='http://proxy.test', retries=0)
        self.assertEqual([result['url'] for result in results], urls)
        self.assertEqual(set(direct_calls), set(urls))
        self.assertTrue(all(result['via'] == 'direct_fallback' for result in results))

    def test_fallback_can_be_disabled(self):
        with patch.object(checker, 'check_url', return_value={'url': 'http://x', 'is_live': False}) as check:
            result = checker.check_urls_parallel(
                ['http://x'], workers=1, proxy='http://proxy.test', retries=0, use_proxy_fallback=False
            )[0]
        self.assertEqual(check.call_count, 1)
        self.assertEqual(result['via'], 'proxy')

    def test_invalid_limits_are_rejected(self):
        with self.assertRaises(ValueError):
            checker.check_url(self.base + '/raw', timeout=0)
        with self.assertRaises(ValueError):
            checker.check_urls_parallel([], workers=0)


if __name__ == '__main__':
    unittest.main()
