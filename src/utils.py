import re
import unicodedata

def normalize_name(name: str) -> str:
    """Normalize channel name for deduplication"""
    if not name:
        return ""
    # Remove group-title, tvg, etc if present in EXTINF line, keep only after comma
    if "," in name:
        # If name is full EXTINF line, take after last comma
        # e.g. #EXTINF:-1 group-title="BD" tvg-name="X",Channel Name
        # We want "Channel Name"
        if "#EXTINF" in name:
            parts = name.split(",", 1)
            name = parts[1] if len(parts) > 1 else name
    name = name.strip()
    # Lowercase
    name = name.lower()
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name)
    # Remove common suffixes that cause duplicates: hd, fhd, sd, 4k, hevc, etc? Keep but normalize
    # Remove special chars except alphanumeric and spaces
    name = re.sub(r'[^a-z0-9 ]', '', name)
    name = name.strip()
    return name

def parse_m3u(file_path):
    """Parse m3u file, return list of dicts: {extinf, name, url, group}"""
    channels = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [l.strip() for l in f if l.strip()]
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            extinf = lines[i]
            # Extract name
            name = extinf.split(",", 1)[1] if "," in extinf else "Unknown"
            # Extract group-title
            group_match = re.search(r'group-title="([^"]*)"', extinf)
            group = group_match.group(1) if group_match else "Unknown"
            # Next line should be URL
            if i+1 < len(lines):
                url = lines[i+1]
                if url.startswith("http"):
                    channels.append({
                        "extinf": extinf,
                        "name": name.strip(),
                        "normalized": normalize_name(name),
                        "url": url.strip(),
                        "group": group.strip(),
                    })
    return channels

def extract_country_from_url_or_group(group, url, geo_map=None):
    """Simple country detection from group-title or geo_map"""
    # If you have geo_map dict ip -> country, use it
    # Fallback: check group/title for country codes
    group_lower = group.lower()
    # Common patterns
    if "bd" in group_lower or "bangla" in group_lower or "bengali" in group_lower:
        return "BD"
    if "in" in group_lower or "india" in group_lower or "hindi" in group_lower:
        return "IN"
    if "pk" in group_lower or "pakistan" in group_lower:
        return "PK"
    if "co" == group_lower or "colombia" in group_lower:
        return "CO"
    if "us" in group_lower or "usa" in group_lower:
        return "US"
    # Try geo_map if provided
    if geo_map:
        # Extract IP from URL
        try:
            ip = url.split("/")[2].split(":")[0]
            if ip in geo_map:
                return geo_map[ip].get("countryCode", "Unknown")
        except:
            pass
    return "Unknown"
