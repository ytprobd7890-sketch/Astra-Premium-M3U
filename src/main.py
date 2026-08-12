"""
Astra Premium M3U Bot — Main
- Reads ULTIMATE_LIVE_*.m3u
- Groups by normalized channel name (duplicate detection)
- Checks each URL for LIVE (parallel, via BD proxy if provided)
- Picks BEST live URL per channel (fastest latency)
- Generates premium playlists

Usage:
  python src/main.py
  BD_PROXY=socks5://user:pass@ip:port python src/main.py
"""

import os
import json
import yaml
import time
from datetime import datetime
from pathlib import Path

from utils import parse_m3u
from checker import check_urls_parallel
from deduplicator import deduplicate_and_pick_best

# Load config
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    # Simple env var substitution for ${VAR}
    import re
    content = f.read()
    # Replace ${VAR} with env var
    def replacer(m):
        var = m.group(1)
        return os.getenv(var, "")
    content = re.sub(r'\${([^}]+)}', replacer, content)
    config = yaml.safe_load(content)

INPUT_FILE = Path(__file__).parent.parent / config['input']['file']
OUTPUT_PREMIUM = Path(__file__).parent.parent / config['output']['premium']
OUTPUT_STATS = Path(__file__).parent.parent / config['output']['stats_json']
OUTPUT_DUP = Path(__file__).parent.parent / config['output']['duplicate_report']
OUTPUT_FINAL = Path(__file__).parent.parent / config['output']['final_checked']

CHECKER_CFG = config['checker']
DEDUP_CFG = config['deduplicator']

def main():
    print("="*60)
    print("🎬 Astra Premium M3U Bot — Starting")
    print(f"Time: {datetime.now().isoformat()}")
    print("="*60)

    # 1. Check input file exists
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        # Try to download from URL if provided
        input_url = config['input'].get('url')
        if input_url:
            print(f"Downloading from {input_url}...")
            import requests
            r = requests.get(input_url, timeout=30)
            INPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            INPUT_FILE.write_bytes(r.content)
        else:
            print("No input URL configured, exiting")
            return

    # 2. Parse M3U
    print(f"\n📖 Parsing {INPUT_FILE}...")
    channels = parse_m3u(str(INPUT_FILE))
    print(f"Found {len(channels)} channel entries")
    unique_urls = len(set(c['url'] for c in channels))
    print(f"Unique URLs: {unique_urls}")

    # 3. Check URLs for LIVE
    urls = list(set(c['url'] for c in channels))
    proxy = CHECKER_CFG.get('proxy') or os.getenv("BD_PROXY")
    if proxy:
        print(f"\n🔌 Using proxy: {proxy[:30]}... (BD Resi)")
    else:
        print("\n🌐 No proxy, using direct (may be blocked for PK/BD)")

    print(f"\n🔍 Checking {len(urls)} URLs for LIVE (workers={CHECKER_CFG['workers']}, timeout={CHECKER_CFG['timeout']}s)...")
    start = time.time()
    results = check_urls_parallel(
        urls,
        timeout=CHECKER_CFG['timeout'],
        workers=CHECKER_CFG['workers'],
        proxy=proxy if proxy else None,
        retries=CHECKER_CFG['retries'],
        use_proxy_fallback=CHECKER_CFG['fallback_direct']
    )
    elapsed = time.time() - start
    live_results = [r for r in results if r['is_live']]
    dead_results = [r for r in results if not r['is_live']]

    print(f"Checked {len(results)} URLs in {elapsed:.1f}s")
    print(f"✅ LIVE: {len(live_results)} | ❌ DEAD: {len(dead_results)} | Live%: {len(live_results)/len(results)*100:.1f}%")

    # Build check_results_map
    check_map = {r['url']: r for r in results}

    # 4. Deduplicate + Pick Best
    print(f"\n♻️  Deduplicating by normalized name (mode={DEDUP_CFG['mode']}, pick={DEDUP_CFG['pick_best_by']})...")
    best_channels, duplicate_report = deduplicate_and_pick_best(
        channels,
        check_map,
        pick_by=DEDUP_CFG['pick_best_by']
    )
    print(f"Original channel names: {len(channels)}")
    print(f"Unique normalized names: {len(set(c['normalized'] for c in channels))}")
    print(f"After deduplication (best live per name): {len(best_channels)}")
    print(f"Duplicate groups found: {len(duplicate_report)}")

    # 5. Generate Premium M3U
    print(f"\n📝 Generating {OUTPUT_PREMIUM}...")
    OUTPUT_PREMIUM.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PREMIUM, 'w', encoding='utf-8') as out:
        out.write("#EXTM3U\n")
        # Sort by name
        for ch in sorted(best_channels, key=lambda x: x['name'].lower()):
            # Use original EXTINF but ensure group-title preserved, and add duplicate count info
            extinf = ch['extinf']
            # Optionally add comment about duplicates
            # out.write(f"# Duplicate count: {ch.get('_duplicates',1)}\n")
            out.write(f"{extinf}\n{ch['url']}\n")

    print(f"✅ Premium M3U written: {len(best_channels)} channels -> {OUTPUT_PREMIUM}")

    # 6. Generate by_country / by_group if possible
    # Simple grouping by first letter or by original group
    by_country_dir = Path(__file__).parent.parent / config['output']['by_country']
    by_country_dir.mkdir(parents=True, exist_ok=True)
    from collections import defaultdict
    country_groups = defaultdict(list)
    for ch in best_channels:
        # Use group field as country hint, or parse from extinf
        country = "Unknown"
        # Try to infer from group-title
        gt = ch.get('group', '').lower()
        if 'bd' in gt or 'bangla' in gt:
            country = 'BD'
        elif 'in' in gt or 'india' in gt:
            country = 'IN'
        elif 'pk' in gt:
            country = 'PK'
        elif 'co' in gt or 'colombia' in gt:
            country = 'CO'
        elif 'us' in gt:
            country = 'US'
        else:
            # Fallback: use first part of normalized? Keep Unknown
            country = ch.get('group', 'Unknown')[:2].upper() if ch.get('group') else 'Unknown'
            if len(country) != 2:
                country = 'Other'
        country_groups[country].append(ch)

    for country, ch_list in country_groups.items():
        out_path = by_country_dir / f"{country}.m3u"
        with open(out_path, 'w', encoding='utf-8') as out:
            out.write("#EXTM3U\n")
            for ch in sorted(ch_list, key=lambda x: x['name'].lower()):
                out.write(f"{ch['extinf']}\n{ch['url']}\n")
    print(f"✅ By country playlists: {len(country_groups)} files in {by_country_dir}")

    # 7. Stats JSON
    stats = {
        "timestamp": datetime.now().isoformat(),
        "input_file": str(INPUT_FILE),
        "total_entries": len(channels),
        "unique_urls": unique_urls,
        "checked": len(results),
        "live": len(live_results),
        "dead": len(dead_results),
        "live_pct": round(len(live_results)/len(results)*100, 1) if results else 0,
        "unique_normalized": len(set(c['normalized'] for c in channels)),
        "after_dedup_best": len(best_channels),
        "duplicate_groups": len(duplicate_report),
        "elapsed_sec": round(elapsed, 1),
        "proxy_used": bool(proxy),
    }
    OUTPUT_STATS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_STATS, 'w', encoding='utf-8') as out:
        json.dump(stats, out, indent=2)
    print(f"✅ Stats: {OUTPUT_STATS}")

    if DEDUP_CFG['keep_report']:
        with open(OUTPUT_DUP, 'w', encoding='utf-8') as out:
            json.dump(duplicate_report, out, indent=2)
        print(f"✅ Duplicate report: {OUTPUT_DUP}")

    # 8. Final checked (same as premium for now, but could be all live not deduped)
    OUTPUT_FINAL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FINAL, 'w', encoding='utf-8') as out:
        out.write("#EXTM3U\n")
        for r in live_results:
            # Find original channel for this URL to get name
            orig = next((c for c in channels if c['url'] == r['url']), None)
            name = orig['name'] if orig else "Unknown"
            extinf = orig['extinf'] if orig else f'#EXTINF:-1,{name}'
            out.write(f"{extinf}\n{r['url']}\n")
    print(f"✅ Final checked (all live, before dedup): {OUTPUT_FINAL} -> {len(live_results)} channels")

    print("\n" + "="*60)
    print(f"🎉 DONE — Premium: {len(best_channels)} channels, Live%: {stats['live_pct']}%")
    print(f"Output: {OUTPUT_PREMIUM}")
    print("="*60)

if __name__ == "__main__":
    main()
