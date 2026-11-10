import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from http_fixtures import fixture_server


ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = ('ip2country-v4.tsv.gz', 'ip2country-v6.tsv.gz')


class CommandLineTests(unittest.TestCase):
    def test_workflow_command_creates_only_one_playlist_and_keeps_duplicates(self):
        with tempfile.TemporaryDirectory() as directory, fixture_server() as server:
            root = Path(directory)
            (root / 'src').mkdir()
            (root / 'playlists').mkdir()
            (root / 'src/data').mkdir()
            for filename in ('main.py', 'checker.py', 'utils.py', 'splitter.py', 'geoip.py', 'countries.py'):
                shutil.copy2(ROOT / 'src' / filename, root / 'src' / filename)
            for filename in DATA_FILES:
                shutil.copy2(ROOT / 'src/data' / filename, root / 'src/data' / filename)
            (root / 'config.yaml').write_text(
                'input:\n  file: "playlists/source.m3u"\n  url: ""\n'
                'output:\n  final_checked: "playlists/FINAL_ULTIMATE_LIVE_CHECKED.m3u"\n'
                '  by_server_country: "playlists/by_country"\n  countries: true\n'
                'checker:\n  timeout: 2\n  workers: 3\n  retries: 0\n'
                '  deep_check: true\n  proxy: "${BD_PROXY}"\n  fallback_direct: true\n',
                encoding='utf-8',
            )
            live = f'#EXTINF:-1,বাংলা TV [1.2.3.4:8000]\n{server.base_url}/valid.m3u8\n'
            dead = f'#EXTINF:-1,Dead\n{server.base_url}/missing.m3u8\n'
            original = '#EXTM3U\n' + live + live + dead
            source = root / 'playlists/source.m3u'
            source.write_text(original, encoding='utf-8')
            summary = root / 'summary.md'
            env = os.environ.copy()
            env.update({'BD_PROXY': '', 'GITHUB_STEP_SUMMARY': str(summary)})

            result = subprocess.run(
                [sys.executable, 'src/main.py'], cwd=root, env=env,
                text=True, capture_output=True, timeout=15,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(source.read_text(encoding='utf-8'), original)
            self.assertEqual(
                (root / 'playlists/FINAL_ULTIMATE_LIVE_CHECKED.m3u').read_text(encoding='utf-8'),
                '#EXTM3U\n' + live + live,
            )
            self.assertEqual({p.name for p in (root / 'playlists').iterdir() if p.is_file()}, {
                'source.m3u', 'FINAL_ULTIMATE_LIVE_CHECKED.m3u',
            })
            # The loopback fixture has no public server country, so the two
            # duplicates land in the unknown-country playlist, not in a real one.
            self.assertEqual({p.name for p in (root / 'playlists/by_country').iterdir()}, {
                'COUNTRY_MASTER.m3u', 'XX_UNKNOWN.m3u', 'README.md',
            })
            unknown = (root / 'playlists/by_country/XX_UNKNOWN.m3u').read_text(encoding='utf-8')
            self.assertEqual(unknown.count('#EXTINF'), 2)
            self.assertIn('group-title="🇺🇳 অজানা সার্ভার (XX)"', unknown)
            self.assertIn('Live entries (duplicates retained): 2', summary.read_text(encoding='utf-8'))
            self.assertEqual(server.hits['/valid.m3u8'], 1)


if __name__ == '__main__':
    unittest.main()
