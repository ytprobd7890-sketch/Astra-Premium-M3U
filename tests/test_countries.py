import ipaddress
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import countries
import geoip
import splitter


class CountryNameTests(unittest.TestCase):
    def test_known_codes_have_bangla_names_and_flags(self):
        self.assertEqual(countries.country_name('BD'), 'বাংলাদেশ')
        self.assertEqual(countries.country_english_name('BD'), 'Bangladesh')
        self.assertEqual(countries.flag('BD'), '🇧🇩')
        self.assertEqual(countries.group_title('PK'), '🇵🇰 পাকিস্তান (PK)')
        self.assertEqual(countries.file_stem('DO'), 'DO_DOMINICAN_REPUBLIC')

    def test_unknown_and_missing_codes_never_show_a_bare_code(self):
        self.assertEqual(countries.group_title(countries.UNKNOWN_CODE), '🇺🇳 অজানা সার্ভার (XX)')
        self.assertEqual(countries.file_stem('ZZ'), 'ZZ_ZZ')
        self.assertEqual(countries.country_name('ZZ'), 'ZZ')

    def test_bangla_collation_sorts_letters_the_way_bangla_is_taught(self):
        names = ['হন্ডুরাস', 'বাংলাদেশ', 'পাকিস্তান', 'কলম্বিয়া', 'ইকুয়েডর']
        self.assertEqual(
            sorted(names, key=countries.collation_key),
            ['ইকুয়েডর', 'কলম্বিয়া', 'পাকিস্তান', 'বাংলাদেশ', 'হন্ডুরাস'],
        )


class GeoLookupTests(unittest.TestCase):
    def test_reserved_addresses_are_never_assigned_to_a_country(self):
        private = (
            '10.0.0.1', '127.0.0.1', '192.168.1.1', '169.254.1.1', '224.0.0.1',
            '255.255.255.255', '::1', 'fe80::1', 'fc00::1', '2001:db8::1', '::ffff:127.0.0.1',
        )
        for address in private:
            with self.subTest(address=address):
                self.assertTrue(geoip.is_private(ipaddress.ip_address(address)))
                self.assertEqual(geoip.lookup_ip(address), countries.UNKNOWN_CODE)

    def test_public_addresses_resolve_from_the_offline_index(self):
        # Stable DB-IP answers that do not depend on the runner's network.
        self.assertEqual(geoip.lookup_ip('1.1.1.1'), 'AU')
        self.assertEqual(geoip.lookup_ip('103.253.18.58'), 'PK')
        self.assertEqual(geoip.lookup_ip('103.119.94.1'), 'BD')

    def test_invalid_input_is_unknown_instead_of_an_exception(self):
        self.assertEqual(geoip.lookup_ip('not-an-address'), countries.UNKNOWN_CODE)
        self.assertEqual(geoip.lookup_host(''), (countries.UNKNOWN_CODE, ''))
        self.assertEqual(geoip.host_of('http://[broken'), '')
        self.assertEqual(geoip.host_of('http://Example.TEST:8000/live.m3u8'), 'example.test')

    def test_hostname_lookup_uses_the_resolved_address(self):
        with patch.object(geoip, 'resolve_host', return_value=('103.253.18.58',)):
            self.assertEqual(geoip.lookup_host('tv.example.test'), ('PK', '103.253.18.58'))
        # A host with only private addresses is grouped as unknown, not guessed.
        with patch.object(geoip, 'resolve_host', return_value=('10.0.0.5',)):
            self.assertEqual(geoip.lookup_host('lan.example.test'), (countries.UNKNOWN_CODE, '10.0.0.5'))

    def test_dns_failure_is_reported_once_and_counted_as_unknown(self):
        with patch.object(geoip, 'resolve_host', return_value=()):
            with patch('builtins.print') as printed:
                geoip._WARNED.clear()
                self.assertEqual(geoip.lookup_host('dead.example.test')[0], countries.UNKNOWN_CODE)
                geoip.lookup_host('dead.example.test')
                warnings = [call.args[0] for call in printed.call_args_list if 'DNS lookup failed' in call.args[0]]
        self.assertEqual(len(warnings), 1)


class ExtinfTests(unittest.TestCase):
    def test_names_with_commas_and_quoted_attributes_survive(self):
        line = '#EXTINF:-1 tvg-id="a,b" tvg-name="A, B" group-title="Old",Name, with comma'
        self.assertEqual(splitter.parse_extinf(line), ('-1', {'tvg-id': 'a,b', 'tvg-name': 'A, B', 'group-title': 'Old'}, 'Name, with comma'))
        rebuilt = splitter.build_extinf(line, 'BD')
        self.assertEqual(
            rebuilt,
            '#EXTINF:-1 group-title="🇧🇩 বাংলাদেশ (BD)" tvg-country="BD" tvg-id="a,b" tvg-name="A, B",Name, with comma',
        )

    def test_unquoted_attributes_and_missing_names_are_handled(self):
        self.assertEqual(splitter.parse_extinf('#EXTINF:-1 tvg-name=Plain,Name'), ('-1', {'tvg-name': 'Plain'}, 'Name'))
        self.assertEqual(splitter.parse_extinf('#EXTINF:-1,বাংলা টিভি'), ('-1', {}, 'বাংলা টিভি'))
        rebuilt = splitter.build_extinf('#EXTINF:-1,বাংলা টিভি', 'PK')
        self.assertEqual(rebuilt, '#EXTINF:-1 group-title="🇵🇰 পাকিস্তান (PK)" tvg-country="PK",বাংলা টিভি')
        self.assertEqual(splitter.parse_extinf('# not an extinf'), ('', {}, ''))


class CountrySplitTests(unittest.TestCase):
    def make_channels(self):
        return [
            {'extinf': '#EXTINF:-1,One', 'directives': [], 'url': 'http://1.1.1.1/a', 'country': 'PK', 'host': '1.1.1.1'},
            {'extinf': '#EXTINF:-1,Two', 'directives': [], 'url': 'http://2.2.2.2/b', 'country': 'BD', 'host': '2.2.2.2'},
            {'extinf': '#EXTINF:-1,Three', 'directives': ['#EXTVLCOPT:http-user-agent=Test'], 'url': 'http://3.3.3.3/c', 'country': 'PK', 'host': '3.3.3.3'},
            {'extinf': '#EXTINF:-1,Four', 'directives': [], 'url': 'http://10.0.0.1/d', 'country': countries.UNKNOWN_CODE, 'host': '10.0.0.1'},
        ]

    def test_pinned_country_comes_first_then_bangla_order_then_unknown(self):
        groups = splitter.group_by_country(self.make_channels())
        self.assertEqual(list(groups), ['BD', 'PK', countries.UNKNOWN_CODE])
        self.assertEqual(len(groups['PK']), 2)

    def test_files_keep_order_directives_and_duplicates(self):
        duplicate = {'extinf': '#EXTINF:-1,One', 'directives': [], 'url': 'http://1.1.1.1/a', 'country': 'PK', 'host': '1.1.1.1'}
        channels = self.make_channels() + [duplicate]
        summary = splitter.country_summary(channels)
        self.assertEqual([(item['code'], item['entries'], item['servers']) for item in summary],
                         [('BD', 1, 1), ('PK', 3, 2), ('XX', 1, 1)])
        with tempfile.TemporaryDirectory() as directory:
            splitter.write_country_files(Path(directory), channels, ['#EXTM3U'])
            pakistan = (Path(directory) / 'PK_PAKISTAN.m3u').read_text(encoding='utf-8')
            master = (Path(directory) / 'COUNTRY_MASTER.m3u').read_text(encoding='utf-8')
            unknown = (Path(directory) / 'XX_UNKNOWN.m3u').read_text(encoding='utf-8')
            bangladesh = (Path(directory) / 'BD_BANGLADESH.m3u').read_text(encoding='utf-8')
        self.assertEqual(pakistan.count('#EXTINF'), 3)
        self.assertEqual(pakistan.count('#EXTGRP:🇵🇰 পাকিস্তান (PK)'), 3)  # players ignoring group-title
        self.assertIn('#EXTVLCOPT:http-user-agent=Test', pakistan)
        self.assertEqual(master.count('#EXTINF'), 5)
        self.assertEqual(unknown.count('#EXTINF'), 1)
        self.assertEqual(bangladesh.count('#EXTINF'), 1)
        self.assertTrue(master.startswith('#EXTM3U\n# Astra server-IP country master'))
        self.assertLess(master.index('🇧🇩'), master.index('🇵🇰'))

    def test_stale_country_files_are_removed_but_other_files_are_kept(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'FR_FRANCE.m3u').write_text('#EXTM3U\n', encoding='utf-8')
            (folder / 'notes.txt').write_text('keep me', encoding='utf-8')
            (folder / 'custom.m3u').write_text('#EXTM3U\n', encoding='utf-8')
            (folder / 'README.md').write_text('old table', encoding='utf-8')
            splitter.write_country_files(folder, self.make_channels(), ['#EXTM3U'])
            names = {path.name for path in folder.iterdir()}
            self.assertIn('PK_PAKISTAN.m3u', (folder / 'README.md').read_text(encoding='utf-8'))
        self.assertNotIn('FR_FRANCE.m3u', names)
        self.assertIn('notes.txt', names)
        self.assertIn('README.md', names)
        self.assertIn('custom.m3u', names)
        self.assertEqual(names & {'COUNTRY_MASTER.m3u', 'BD_BANGLADESH.m3u', 'PK_PAKISTAN.m3u', 'XX_UNKNOWN.m3u'},
                         {'COUNTRY_MASTER.m3u', 'BD_BANGLADESH.m3u', 'PK_PAKISTAN.m3u', 'XX_UNKNOWN.m3u'})


if __name__ == '__main__':
    unittest.main()
