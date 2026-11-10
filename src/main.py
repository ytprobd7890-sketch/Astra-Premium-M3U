"""Check the source playlist and publish live entries grouped by server country."""

import os
import random
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

import splitter
from checker import check_urls_parallel
from utils import parse_m3u, read_preamble


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / 'config.yaml'


def load_config(path=CONFIG_PATH):
    """Expand environment variables after parsing YAML to protect secrets."""
    with open(path, encoding='utf-8') as source:
        data = yaml.safe_load(source)

    def expand(value):
        if isinstance(value, dict):
            return {key: expand(item) for key, item in value.items()}
        if isinstance(value, list):
            return [expand(item) for item in value]
        if isinstance(value, str):
            return re.sub(r'\${([^}]+)}', lambda match: os.getenv(match.group(1), ''), value)
        return value

    return expand(data)


config = load_config()
INPUT_FILE = ROOT / config['input']['file']
OUTPUT_FINAL = ROOT / config['output']['final_checked']
OUTPUT_COUNTRIES = ROOT / config['output']['by_server_country']
COUNTRIES_ENABLED = bool(config['output'].get('countries', True))
CHECKER_CFG = config['checker']


def _write_channel(out, channel):
    out.write(f"{channel['extinf']}\n")
    for directive in channel['directives']:
        out.write(f'{directive}\n')
    out.write(f"{channel['url']}\n")


def _write_playlist(path, preamble, channels):
    """Replace the output only after the whole playlist has been written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', newline='\n', dir=path.parent,
            prefix=f'.{path.name}.', suffix='.tmp', delete=False,
        ) as out:
            temp_path = Path(out.name)
            for line in preamble:
                out.write(f'{line}\n')
            for channel in channels:
                _write_channel(out, channel)
        if path.exists():
            os.chmod(temp_path, path.stat().st_mode & 0o777)
        temp_path.replace(path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _write_action_summary(stats):
    """Show counts in Actions without creating another published output file."""
    summary_path = os.getenv('GITHUB_STEP_SUMMARY')
    if not summary_path:
        return
    with open(summary_path, 'a', encoding='utf-8') as summary:
        summary.write('## Hourly live stream check\n\n')
        summary.write(f"- Source entries: {stats['total_entries']}\n")
        summary.write(f"- Checked: {stats['checked']} unique URLs\n")
        summary.write(f"- Live URLs: {stats['live']}\n")
        summary.write(f"- Dead or unreachable URLs: {stats['dead']}\n")
        summary.write(f"- Live entries (duplicates retained): {stats['live_entries']}\n")
        summary.write(f"- Completed: {stats['timestamp']}\n")
        countries = stats.get('countries') or []
        if countries:
            summary.write(
                f"\n### Live entries by server country ({stats['country_total']})\n\n"
                '| Country | Group | Servers | Entries | File |\n'
                '| --- | --- | ---: | ---: | --- |\n'
            )
            for country in countries:
                summary.write(
                    f"| {country['name']} ({country['code']}) | {country['group_title']} "
                    f"| {country['servers']} | {country['entries']} | `{country['file']}` |\n"
                )


def main(countries_enabled=None):
    countries_enabled = COUNTRIES_ENABLED if countries_enabled is None else countries_enabled
    print('=' * 60)
    print('🎬 All Live Streams — Hourly Check')
    print(f'Time: {datetime.now(timezone.utc).isoformat()}')
    print('=' * 60)

    if INPUT_FILE.resolve() == OUTPUT_FINAL.resolve():
        raise SystemExit('Input and output must be different files; the source was not changed.')
    if countries_enabled and INPUT_FILE.resolve().parent == OUTPUT_COUNTRIES.resolve():
        raise SystemExit('The country output folder must not be the input folder; nothing was changed.')
    if not INPUT_FILE.exists():
        input_url = config['input'].get('url')
        if not input_url:
            raise SystemExit(f'Input file not found: {INPUT_FILE}')
        print('Downloading the configured input playlist...')
        import requests
        response = requests.get(input_url, timeout=30)
        response.raise_for_status()
        INPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        INPUT_FILE.write_bytes(response.content)

    print(f'\n📖 Parsing {INPUT_FILE}...')
    try:
        channels = parse_m3u(INPUT_FILE, strict=True)
    except ValueError as error:
        raise SystemExit(f'{error}; the existing playlist was not changed.') from error
    if not channels:
        raise SystemExit('Input has no HTTP(S) channel entries; the existing playlist was not changed.')
    preamble = read_preamble(INPUT_FILE)

    # Identical URLs can share one network probe, but every live source entry is
    # written back separately, including exact duplicates and repeated names.
    urls = list(dict.fromkeys(channel['url'] for channel in channels))
    random.Random(0).shuffle(urls)  # Avoid contacting one host in a large block.
    print(f'Found {len(channels)} entries and {len(urls)} unique URLs')

    proxy = CHECKER_CFG.get('proxy') or os.getenv('BD_PROXY') or None
    print('\n🔌 Using configured proxy' if proxy else '\n🌐 Using a direct connection')
    print(
        f"🔍 Checking {len(urls)} URLs (workers={CHECKER_CFG['workers']}, "
        f"timeout={CHECKER_CFG['timeout']}s, deep_check={CHECKER_CFG.get('deep_check', False)})..."
    )
    started = time.monotonic()
    results = check_urls_parallel(
        urls,
        timeout=CHECKER_CFG['timeout'],
        workers=CHECKER_CFG['workers'],
        proxy=proxy,
        retries=CHECKER_CFG['retries'],
        use_proxy_fallback=CHECKER_CFG['fallback_direct'],
        deep_check=CHECKER_CFG.get('deep_check', False),
    )
    elapsed = time.monotonic() - started
    if len(results) != len(urls) or {result['url'] for result in results} != set(urls):
        raise SystemExit('Not every source URL was checked; the existing playlist was not changed.')
    live_results = [result for result in results if result['is_live']]
    if not live_results:
        raise SystemExit(
            'No streams could be verified. The existing playlist was not changed; '
            'check the runner network, proxy, and source playlist.'
        )

    check_map = {result['url']: result for result in results}
    live_channels = [channel for channel in channels if check_map[channel['url']]['is_live']]
    _write_playlist(OUTPUT_FINAL, preamble, live_channels)

    country_files = []
    if countries_enabled:
        print('\n🌍 Resolving the country of every live server IP (offline DB-IP index)...')
        splitter.assign_countries(live_channels)
        country_files = splitter.write_country_files(OUTPUT_COUNTRIES, live_channels, preamble)

    stats = {
        'timestamp': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'total_entries': len(channels),
        'checked': len(results),
        'live': len(live_results),
        'dead': len(results) - len(live_results),
        'live_entries': len(live_channels),
        'elapsed_sec': round(elapsed, 1),
        'countries': country_files,
        'country_total': len(country_files),
    }
    _write_action_summary(stats)
    print(f"✅ Live URLs: {stats['live']} | Unreachable: {stats['dead']} | {elapsed:.1f}s")
    print(f"✅ All live entries (duplicates retained): {stats['live_entries']} -> {OUTPUT_FINAL}")
    if countries_enabled:
        for country in country_files:
            print(
                f"   {country['group_title']}: {country['entries']} entries "
                f"({country['servers']} servers) -> {OUTPUT_COUNTRIES / country['file']}"
            )
        print(f"   Master by country -> {OUTPUT_COUNTRIES / 'COUNTRY_MASTER.m3u'}")
    return stats


if __name__ == '__main__':
    main()
