import re
import unicodedata

def clean_display_name(name: str) -> str:
    """Clean display name: remove unprofessional bracket IP and extra junk, but keep HD etc"""
    if not name:
        return ""
    # If full EXTINF line, extract after comma for name part
    if "#EXTINF" in name and "," in name:
        name = name.split(",", 1)[1]
    name = name.strip()
    # Remove bracket pattern like " [103.253.18.58:8000]" or " [38.52...]" at end
    name = re.sub(r'\s*\[.*?\]\s*$', '', name).strip()
    # Remove multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def normalize_name(name: str) -> str:
    """Normalize channel name for deduplication - aggressive to group duplicates"""
    if not name:
        return ""
    # If full EXTINF line, take after comma
    if "#EXTINF" in name and "," in name:
        name = name.split(",", 1)[1]
    name = name.strip()

    # Remove bracket pattern at end: " [xxx]" or " (xxx)"
    name = re.sub(r'\s*[\[\(].*?[\]\)]\s*$', '', name)

    # Remove price pattern: " - Rs 19.00", " - Rs19", " Rs 19.00" at end
    name = re.sub(r'\s*-\s*Rs\.?\s*\d+(\.\d+)?\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*Rs\.?\s*\d+(\.\d+)?\s*$', '', name, flags=re.IGNORECASE)
    # Also remove " - Rs 0.10" etc anywhere at end
    name = re.sub(r'\s*-\s*Rs.*$', '', name, flags=re.IGNORECASE)

    # Lowercase for grouping
    name = name.lower()

    # Remove quality suffixes for grouping purposes to merge HD/SD versions
    # e.g., "somoy tv hd" -> "somoy tv", "star plus hd" -> "star plus"
    # This helps deduplicate HD/SD same channel
    name = re.sub(r'\s+(fhd|uhd|hd|sd|4k|8k|hevc|h264|h265|full hd|ultra hd|hdtv)\s*$', '', name)
    # Also remove leading "ro: ", "pk:", etc
    name = re.sub(r'^(ro|pk|bd|in|us|uk|es|fr|de|it|pt|tr|ar|co|cl|pe|ec|mx|br)\s*:\s*', '', name)

    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name)

    # Remove special chars except alphanumeric and spaces for key
    name_key = re.sub(r'[^a-z0-9 ]', '', name)
    name_key = name_key.strip()

    # Remove very short duplicates like "tv" alone? Keep
    return name_key

def parse_m3u(file_path):
    """Parse m3u file, return list of dicts: {extinf, name, display_name, normalized, url, group}"""
    channels = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [l.strip() for l in f if l.strip()]
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            original_extinf = lines[i]
            # Extract name after comma
            raw_name = original_extinf.split(",", 1)[1] if "," in original_extinf else "Unknown"
            # Clean display name (remove bracket, keep HD etc)
            display_name = clean_display_name(raw_name)

            # Normalized for deduplication (aggressive)
            normalized = normalize_name(raw_name)

            # Extract group-title
            group_match = re.search(r'group-title="([^"]*)"', original_extinf)
            group = group_match.group(1) if group_match else "Unknown"

            # Clean group-title too (remove IP if it's IP:PORT)
            # If group-title looks like IP:PORT, set to Unknown
            if re.match(r'^\d+\.\d+\.\d+\.\d+:\d+$', group):
                group = "Unknown"

            # Build clean EXTINF without bracket in name, and without IP group if needed
            # Keep original attributes except tvg-name? We'll keep original prefix but replace name
            # Reconstruct: keep everything before comma, then clean display name
            prefix = original_extinf.split(",", 1)[0] if "," in original_extinf else "#EXTINF:-1"
            # Also clean group-title if it's IP:PORT -> set to display_name's first word or Unknown
            # For professional look, we will keep group-title as is unless it's IP, then set to "General"
            if re.match(r'^\d+\.\d+\.\d+\.\d+:\d+$', group):
                # Replace group-title with General
                prefix = re.sub(r'group-title="[^"]*"', 'group-title="General"', prefix)

            clean_extinf = f"{prefix},{display_name}"

            if i+1 < len(lines):
                url = lines[i+1]
                if url.startswith("http"):
                    channels.append({
                        "extinf": clean_extinf,
                        "original_extinf": original_extinf,
                        "name": display_name,
                        "display_name": display_name,
                        "normalized": normalized,
                        "url": url.strip(),
                        "group": group.strip(),
                    })
    return channels

def extract_country_from_url_or_group(group, url, geo_map=None):
    """Simple country detection"""
    group_lower = group.lower()
    if "bd" in group_lower or "bangla" in group_lower:
        return "BD"
    if "in" in group_lower or "india" in group_lower:
        return "IN"
    if "pk" in group_lower or "pakistan" in group_lower:
        return "PK"
    if group_lower == "co" or "colombia" in group_lower:
        return "CO"
    if geo_map:
        try:
            ip = url.split("/")[2].split(":")[0]
            if ip in geo_map:
                return geo_map[ip].get("countryCode", "Unknown")
        except:
            pass
    return "Unknown"
