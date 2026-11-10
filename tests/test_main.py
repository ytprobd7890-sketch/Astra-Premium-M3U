import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import main as bot
from http_fixtures import fixture_server
from utils import parse_m3u


class BotIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server_context = fixture_server()
        cls.server = cls.server_context.__enter__()
        cls.base = cls.server.base_url

    @classmethod
    def tearDownClass(cls):
        cls.server_context.__exit__(None, None, None)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.m3u'
        self.final = self.root / 'FINAL.m3u'
        self.countries = self.root / 'by_country'
        self.config = {
            'input': {'file': str(self.source), 'url': ''},
            'output': {'by_server_country': str(self.countries), 'countries': True},
        }
        self.checker_config = {
            'timeout': 2, 'workers': 5, 'retries': 0,
            'proxy': '', 'fallback_direct': True, 'deep_check': True,
        }
        with self.server.lock:
            self.server.hits.clear()

    def run_bot(self, output=None, summary_path=None, destination=None,
                countries_enabled=None, countries_dir=None):
        patches = patch.multiple(
            bot, config=self.config, INPUT_FILE=self.source,
            OUTPUT_FINAL=destination if destination is not None else self.final,
            OUTPUT_COUNTRIES=self.countries if countries_dir is None else countries_dir,
            CHECKER_CFG=self.checker_config,
        )
        env = {'BD_PROXY': '', 'GITHUB_STEP_SUMMARY': str(summary_path) if summary_path else ''}
        with patch.dict(os.environ, env), patches, redirect_stdout(output if output is not None else io.StringIO()):
            return bot.main(countries_enabled=countries_enabled)

    def test_all_live_entries_keep_duplicates_order_and_original_metadata(self):
        preamble = '#EXTM3U x-tvg-url="http://example.test/guide.xml"\n# global option\n'
        repeated = (
            '#EXTINF:-1 group-title="BD, News",বাংলা টিভি [1.2.3.4:8000]\n'
            f'#EXTVLCOPT:http-user-agent=Example\n{self.base}/valid.m3u8\n'
        )
        same_name_different_urls = (
            f'#EXTINF:-1 group-title="US",Sports\n{self.base}/raw\n'
            f'#EXTINF:-1 group-title="IN",Sports\n{self.base}/media2\n'
        )
        alias = f'#EXTINF:-1,Alias\n{self.base}/valid.m3u8\n'
        dead = (
            f'#EXTINF:-1 group-title="PK",Dead\n{self.base}/missing.m3u8\n'
            f'#EXTINF:-1,Error Page\n{self.base}/html\n'
        )
        original = preamble + repeated + repeated + same_name_different_urls + alias + dead
        expected = preamble + repeated + repeated + same_name_different_urls + alias
        self.source.write_text(original, encoding='utf-8')
        summary_path = self.root / 'summary.md'

        stats = self.run_bot(summary_path=summary_path)

        self.assertEqual(self.source.read_text(encoding='utf-8'), original)
        self.assertEqual(self.final.read_text(encoding='utf-8'), expected)
        live = parse_m3u(self.final, strict=True)
        self.assertEqual(len(live), 5)
        self.assertEqual(live[0], live[1])  # Exact duplicate remains twice.
        self.assertEqual(live[2]['extinf'].split(',', 1)[1], 'Sports')
        self.assertEqual(live[3]['extinf'].split(',', 1)[1], 'Sports')
        self.assertNotEqual(live[2]['url'], live[3]['url'])
        self.assertEqual(self.server.hits['/valid.m3u8'], 1)
        self.assertEqual((stats['total_entries'], stats['checked'], stats['live'], stats['dead']), (7, 5, 3, 2))
        self.assertEqual(stats['live_entries'], 5)
        self.assertTrue(stats['timestamp'].endswith('+00:00'))
        summary = summary_path.read_text(encoding='utf-8')
        self.assertIn('Checked: 5 unique URLs', summary)
        self.assertIn('Live entries (duplicates retained): 5', summary)
        self.assertEqual(
            {p.name for p in self.root.iterdir()},
            {'source.m3u', 'FINAL.m3u', 'summary.md', 'by_country'},
        )
        self.assertIn('Live entries by server country', summary)
        self.assertIn('অজানা সার্ভার (XX)', summary)

    def test_no_live_streams_leave_previous_playlist_untouched(self):
        self.source.write_text(f'#EXTM3U\n#EXTINF:-1,Dead\n{self.base}/missing.m3u8\n', encoding='utf-8')
        self.final.write_text('previous final', encoding='utf-8')
        with self.assertRaisesRegex(SystemExit, 'No streams could be verified'):
            self.run_bot()
        self.assertEqual(self.final.read_text(), 'previous final')

    def test_missing_and_empty_input_fail_without_replacing_playlist(self):
        self.final.write_text('previous', encoding='utf-8')
        with self.assertRaisesRegex(SystemExit, 'Input file not found'):
            self.run_bot()
        self.source.write_text('#EXTM3U\n', encoding='utf-8')
        with self.assertRaisesRegex(SystemExit, 'no HTTP\\(S\\) channel entries'):
            self.run_bot()
        self.assertEqual(self.final.read_text(), 'previous')

    def test_unsupported_source_entry_fails_without_partial_publication(self):
        self.source.write_text(
            f'#EXTM3U\n#EXTINF:-1,One\n{self.base}/raw\n#EXTINF:-1,Unsupported\nrtsp://example.test/live\n',
            encoding='utf-8',
        )
        self.final.write_text('previous', encoding='utf-8')
        with self.assertRaisesRegex(SystemExit, 'unsupported HTTP\\(S\\) URL'):
            self.run_bot()
        self.assertEqual(self.final.read_text(), 'previous')
        self.assertEqual(self.server.hits['/raw'], 0)

    def test_incomplete_check_does_not_publish(self):
        self.source.write_text(
            f'#EXTM3U\n#EXTINF:-1,One\n{self.base}/raw\n#EXTINF:-1,Two\n{self.base}/media2\n',
            encoding='utf-8',
        )
        self.final.write_text('previous', encoding='utf-8')
        with patch.object(bot, 'check_urls_parallel', return_value=[{'url': self.base + '/raw', 'is_live': True}]):
            with self.assertRaisesRegex(SystemExit, 'Not every source URL was checked'):
                self.run_bot()
        self.assertEqual(self.final.read_text(), 'previous')

    def test_output_must_not_overwrite_source(self):
        content = f'#EXTM3U\n#EXTINF:-1,One\n{self.base}/raw\n'
        self.source.write_text(content, encoding='utf-8')
        with self.assertRaisesRegex(SystemExit, 'Input and output must be different'):
            self.run_bot(destination=self.source)
        self.assertEqual(self.source.read_text(encoding='utf-8'), content)
        self.assertEqual(self.server.hits['/raw'], 0)

    def test_write_failure_preserves_existing_playlist(self):
        self.source.write_text(f'#EXTM3U\n#EXTINF:-1,One\n{self.base}/raw\n', encoding='utf-8')
        self.final.write_text('previous', encoding='utf-8')
        with patch.object(bot, '_write_channel', side_effect=OSError('disk problem')):
            with self.assertRaisesRegex(OSError, 'disk problem'):
                self.run_bot()
        self.assertEqual(self.final.read_text(), 'previous')
        self.assertEqual(list(self.root.glob('*.tmp')), [])

    def test_proxy_credentials_are_not_printed(self):
        self.source.write_text(f'#EXTM3U\n#EXTINF:-1,One\n{self.base}/raw\n', encoding='utf-8')
        secret = 'socks5h://secret-user:secret-password@proxy.example:1080'
        self.checker_config['proxy'] = secret
        output = io.StringIO()

        def fake_check(urls, **kwargs):
            self.assertEqual(kwargs['proxy'], secret)
            return [{'url': urls[0], 'is_live': True, 'latency_ms': 1, 'size': 1000}]

        with patch.object(bot, 'check_urls_parallel', side_effect=fake_check):
            self.run_bot(output=output)
        self.assertNotIn('secret-user', output.getvalue())
        self.assertNotIn('secret-password', output.getvalue())

    def test_environment_values_are_expanded_after_yaml_is_parsed(self):
        config_file = self.root / 'config.yaml'
        config_file.write_text('checker:\n  proxy: "${BD_PROXY}"\n', encoding='utf-8')
        secret = 'socks5h://user:pa"ss\\word@host:1080'
        with patch.dict(os.environ, {'BD_PROXY': secret}):
            loaded = bot.load_config(config_file)
        self.assertEqual(loaded['checker']['proxy'], secret)

    def test_live_entries_are_grouped_by_the_country_of_the_server_ip(self):
        import geoip
        import splitter

        # 1.2.3.4 is the fixture server host in the source entries, so patch the
        # lookup table instead of the network: two "countries" plus one unknown.
        servers = {
            '1.2.3.4': ('PK', '1.2.3.4'),
            '5.6.7.8': ('BD', '5.6.7.8'),
            'example.test': ('XX', ''),
        }
        original_lookup = geoip.lookup_host
        self.addCleanup(setattr, geoip, 'lookup_host', original_lookup)
        geoip.lookup_host = lambda host: servers.get(host, ('XX', ''))

        self.source.write_text(
            '#EXTM3U\n'
            f'#EXTINF:-1 group-title="Old Group" tvg-name="One",First\n{self.base}/raw\n'
            f'#EXTINF:-1,দুই\n{self.base}/media2\n',
            encoding='utf-8',
        )
        # Both fixture URLs share 127.0.0.1; keep the mapping honest by looking
        # up the host through the patched table below.
        def host_of(url):
            return '1.2.3.4' if url.endswith('/raw') else '5.6.7.8'

        with patch.object(splitter.geoip, 'host_of', side_effect=host_of):
            stats = self.run_bot()

        master = (self.countries / 'COUNTRY_MASTER.m3u').read_text(encoding='utf-8')
        pakistan = (self.countries / 'PK_PAKISTAN.m3u').read_text(encoding='utf-8')
        bangladesh = (self.countries / 'BD_BANGLADESH.m3u').read_text(encoding='utf-8')
        self.assertIn('group-title="🇵🇰 পাকিস্তান (PK)" tvg-country="PK" tvg-name=One,First', pakistan)
        self.assertIn('group-title="🇧🇩 বাংলাদেশ (BD)" tvg-country="BD",দুই', bangladesh)
        self.assertEqual(pakistan.count('#EXTINF'), 1)
        self.assertEqual(bangladesh.count('#EXTINF'), 1)
        self.assertEqual(master.count('#EXTINF'), 2)
        self.assertLess(master.index('বাংলাদেশ'), master.index('পাকিস্তান'))
        self.assertEqual([item['code'] for item in stats['countries']], ['BD', 'PK'])
        self.assertEqual({p.name for p in self.countries.iterdir()}, {
            'COUNTRY_MASTER.m3u', 'BD_BANGLADESH.m3u', 'PK_PAKISTAN.m3u', 'README.md',
        })

    def test_country_output_can_be_switched_off_and_never_overwrites_the_source(self):
        self.source.write_text(f'#EXTM3U\n#EXTINF:-1,One\n{self.base}/raw\n', encoding='utf-8')
        stats = self.run_bot(countries_enabled=False)
        self.assertFalse(self.countries.exists())
        self.assertEqual(stats['countries'], [])

        with self.assertRaisesRegex(SystemExit, 'country output folder must not be'):
            self.run_bot(countries_dir=self.source.parent)
        self.assertEqual(
            self.source.read_text(encoding='utf-8'),
            '#EXTM3U\n#EXTINF:-1,One\n' + self.base + '/raw\n',
        )


if __name__ == '__main__':
    unittest.main()
