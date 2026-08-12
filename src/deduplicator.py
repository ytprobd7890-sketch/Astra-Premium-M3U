from collections import defaultdict
import json
from utils import normalize_name

def group_by_normalized(channels):
    """Group channels by normalized name"""
    grouped = defaultdict(list)
    for ch in channels:
        norm = ch['normalized']
        if not norm:
            continue
        grouped[norm].append(ch)
    return grouped

def pick_best(group, check_results_map, pick_by="fastest"):
    """
    group: list of channel dicts with same normalized name
    check_results_map: dict url -> check result {is_live, latency_ms, size}
    pick_by: fastest, biggest, first
    Returns best channel dict or None
    """
    # Filter only live
    live_channels = []
    for ch in group:
        res = check_results_map.get(ch['url'])
        if res and res.get('is_live'):
            live_channels.append((ch, res))

    if not live_channels:
        return None

    if pick_by == "fastest":
        # Sort by latency
        live_channels.sort(key=lambda x: x[1].get('latency_ms', 9999))
    elif pick_by == "biggest":
        # Sort by size descending
        live_channels.sort(key=lambda x: x[1].get('size', 0), reverse=True)
    elif pick_by == "first":
        # Keep original order
        pass

    best_ch, best_res = live_channels[0]
    # Attach best_res for later use
    best_ch['_check'] = best_res
    best_ch['_duplicates'] = len(group)  # How many duplicates had
    best_ch['_all_urls'] = [c['url'] for c in group]
    return best_ch

def deduplicate_and_pick_best(channels, check_results_map, pick_by="fastest"):
    """
    Main deduplication + best picking
    Returns:
      - best_channels: list of best channels (1 per normalized name)
      - duplicate_report: dict normalized -> {count, all_urls, best_url}
    """
    grouped = group_by_normalized(channels)
    best_channels = []
    duplicate_report = {}

    for norm, group in grouped.items():
        best = pick_best(group, check_results_map, pick_by=pick_by)
        if best:
            best_channels.append(best)
        # Build report if duplicates >1
        if len(group) > 1:
            duplicate_report[norm] = {
                "original_name": group[0]['name'],
                "count": len(group),
                "all_urls": [c['url'] for c in group],
                "best_url": best['url'] if best else None,
                "best_latency": best['_check'].get('latency_ms') if best and '_check' in best else None,
            }

    return best_channels, duplicate_report
