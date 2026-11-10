import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from utils import parse_m3u, read_preamble


class PlaylistParsingTests(unittest.TestCase):
    def test_duplicates_names_metadata_and_directives_are_preserved(self):
        entry = (
            '#EXTINF:-1 group-title="BD, News",বাংলা টিভি [1.2.3.4:8000]\n'
            '#EXTVLCOPT:http-user-agent=Example Player\n'
            'http://example.test/live.m3u8\n'
        )
        content = '#EXTM3U x-tvg-url="http://example.test/guide.xml"\n# global option\n' + entry + entry
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.m3u'
            path.write_text(content, encoding='utf-8')
            channels = parse_m3u(path, strict=True)
            preamble = read_preamble(path)
        self.assertEqual(preamble, ['#EXTM3U x-tvg-url="http://example.test/guide.xml"', '# global option'])
        self.assertEqual(len(channels), 2)
        self.assertEqual(channels[0], channels[1])
        self.assertEqual(channels[0]['extinf'], '#EXTINF:-1 group-title="BD, News",বাংলা টিভি [1.2.3.4:8000]')
        self.assertEqual(channels[0]['directives'], ['#EXTVLCOPT:http-user-agent=Example Player'])

    def test_missing_header_is_added_without_changing_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.m3u'
            path.write_text('# comment\n#EXTINF:-1,Channel\nhttp://example.test/live\n', encoding='utf-8')
            self.assertEqual(read_preamble(path), ['#EXTM3U', '# comment'])
            self.assertEqual(len(parse_m3u(path, strict=True)), 1)

    def test_strict_mode_rejects_unsupported_and_missing_entries(self):
        invalid_playlists = (
            '#EXTM3U\n#EXTINF:-1,Unsupported\nrtsp://example.test/live\n',
            '#EXTM3U\n#EXTINF:-1,Missing\n#EXTINF:-1,Other\nhttp://example.test/live\n',
            '#EXTM3U\n#EXTINF:-1,Missing\n',
            '#EXTM3U\n#EXTINF:-1,Bad\nhttp://example.test/invalid\x00segment\n',
            '#EXTM3U\nhttp://example.test/no-extinf\n',
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.m3u'
            for content in invalid_playlists:
                with self.subTest(content=content):
                    path.write_text(content, encoding='utf-8')
                    with self.assertRaises(ValueError):
                        parse_m3u(path, strict=True)

    def test_non_strict_mode_skips_unsupported_entries(self):
        content = '#EXTM3U\n#EXTINF:-1,Unsupported\nrtsp://example.test/live\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.m3u'
            path.write_text(content, encoding='utf-8')
            self.assertEqual(parse_m3u(path), [])


if __name__ == '__main__':
    unittest.main()
