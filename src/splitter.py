"""Group checked streams by the country of their server IP.

A channel's country is the country of the machine that serves it, not the
country of the channel: a Bangladeshi news channel hosted on a Pakistani
server is listed under Pakistan. That is what makes the result usable - the
files tell you which server geographies your playlist actually depends on.

Entries keep their original ``#EXTINF`` name and directives; only
``group-title`` is rewritten to ``<flag> <Bangla country> (<ISO code>)`` and
``tvg-country`` is added next to it.
"""

import re
from pathlib import Path

import countries
import geoip

# Order used by the master playlist and the summary table.
PINNED_FIRST = countries.PINNED

_NAME_SEPARATOR = ','


def parse_extinf(line):
    """Split ``#EXTINF:duration attrs,name`` into duration, attributes, name.

    Attributes may be quoted (and quoted values may contain commas), and the
    display name after the final comma may contain anything, including commas.
    """
    if not line.startswith('#EXTINF') or ':' not in line:
        return '', {}, ''
    payload = line.split(':', 1)[1]
    length = len(payload)
    position = 0
    while position < length and payload[position] == ' ':
        position += 1
    start = position
    while position < length and payload[position] not in ' ,':
        position += 1
    duration = payload[start:position]

    attrs = {}
    while True:
        while position < length and payload[position].isspace():
            position += 1
        if position >= length or payload[position] == _NAME_SEPARATOR:
            break
        key_start = position
        while position < length and payload[position] not in '=,':
            position += 1
        if position >= length or payload[position] != '=':
            break
        key = payload[key_start:position].strip()
        position += 1
        if position < length and payload[position] == '"':
            closing = payload.find('"', position + 1)
            if closing == -1:
                value, position = payload[position + 1:], length
            else:
                value, position = payload[position + 1:closing], closing + 1
        else:
            value_start = position
            while position < length and payload[position] not in ' ,':
                position += 1
            value = payload[value_start:position]
        if key:
            attrs[key.lower()] = value

    separator = payload.find(_NAME_SEPARATOR, position)
    name = payload[separator + 1:] if separator != -1 else ''
    return duration, attrs, name


def _attribute(key, value):
    value = value.replace('"', "'")
    if re.search(r'[",\s]', value):
        return f'{key}="{value}"'
    return f'{key}={value}'


def build_extinf(line, code):
    """Return the original EXTINF with only the country attributes rewritten."""
    duration, attrs, name = parse_extinf(line)
    if not duration:
        return line
    ordered = [f'group-title="{countries.group_title(code)}"', f'tvg-country="{code}"']
    for key, value in attrs.items():
        if key in ('group-title', 'tvg-country') or not value:
            continue
        ordered.append(_attribute(key, value))
    return f"#EXTINF:{duration} {' '.join(ordered)},{name}"


def assign_countries(channels, channel_key=None):
    """Attach ``country``/``server``/``host`` to each channel and report misses.

    Channels sharing a host share one lookup, and a host is looked up only
    once per run even when thousands of entries use it.
    """
    key = channel_key or (lambda channel: geoip.host_of(channel['url']))
    resolved = {}
    for channel in channels:
        host = key(channel)
        if host not in resolved:
            code, address = geoip.lookup_host(host)
            if not geoip.code_is_known(code):
                code = countries.UNKNOWN_CODE
            resolved[host] = (code, address)
        code, address = resolved[host]
        channel['host'] = host
        channel['country'] = code
        channel['server'] = address or host
    return channels


def sort_key(code, pinned=PINNED_FIRST):
    """Pinned countries first, then Bangla alphabetical order, unknown last."""
    if code == countries.UNKNOWN_CODE:
        return (2, (), code)
    return (
        0 if code in pinned else 1,
        countries.collation_key(countries.country_name(code)),
        code,
    )


def group_by_country(channels, pinned=PINNED_FIRST):
    """Return ``{code: [channels]}`` ordered for display, entries untouched."""
    groups = {}
    for channel in channels:
        groups.setdefault(channel['country'], []).append(channel)
    ordered = {}
    for code in sorted(groups, key=lambda item: sort_key(item, pinned)):
        ordered[code] = groups[code]
    return ordered


def country_summary(channels):
    """Per-country totals that mirror the published files."""
    groups = group_by_country(channels)
    return [
        {
            'code': code,
            'name': countries.country_name(code),
            'english_name': countries.country_english_name(code),
            'group_title': countries.group_title(code),
            'file': f'{countries.file_stem(code)}.m3u',
            'entries': len(entries),
            'servers': len({channel['host'] for channel in entries}),
        }
        for code, entries in groups.items()
    ]


def _header(preamble, filename, entries):
    """Keep the source header and describe what this particular file holds."""
    header = list(preamble)
    code = entries[0]['country'] if entries else countries.UNKNOWN_CODE
    if filename == 'COUNTRY_MASTER.m3u':
        header.append(f'# Astra server-IP country master: {len(entries)} live entries')
        header.append('# Country groups are ordered BD first, then Bangla alphabetical order')
    else:
        header.append(f"# Astra server country: {countries.country_english_name(code)} ({code}) - "
                      f"{len(entries)} live entries")
        header.append(f"# {countries.group_title(code)}")
    return header


def write_country_files(directory, channels, preamble):
    """Write one playlist per country plus the master playlist.

    Files are written to temporary names first and renamed together, so a
    failed write never leaves half of the country files updated.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    groups = group_by_country(channels)
    summary = country_summary(channels)

    staged = []
    try:
        payload = {f'{countries.file_stem(code)}.m3u': entries for code, entries in groups.items()}
        # The master lists one country block after another, in the same order
        # as the per-country files, so a player that ignores group-title still
        # plays countries one after another instead of interleaving them.
        payload['COUNTRY_MASTER.m3u'] = [channel for entries in groups.values() for channel in entries]
        for filename, entries in payload.items():
            target = directory / filename
            temp = directory / f'.{filename}.tmp'
            header = _header(preamble, filename, entries)
            with open(temp, 'w', encoding='utf-8', newline='\n') as out:
                for line in header:
                    out.write(f'{line}\n')
                for channel in entries:
                    out.write(f"{build_extinf(channel['extinf'], channel['country'])}\n")
                    for directive in channel.get('directives', ()):
                        out.write(f'{directive}\n')
                    if not any(directive.upper().startswith('#EXTGRP:') for directive in channel.get('directives', ())):
                        # Players that ignore group-title still get a group tag.
                        out.write(f"#EXTGRP:{countries.group_title(channel['country'])}\n")
                    out.write(f"{channel['url']}\n")
            staged.append((temp, target))
        for temp, target in staged:
            temp.replace(target)
    finally:
        for temp, _ in staged:
            if temp.exists():
                temp.unlink()
    _remove_stale(directory, set(payload))
    _write_readme(directory, summary, len(channels))
    return summary


def _write_readme(directory, summary, total):
    """Describe the published files so the folder explains itself on GitHub."""
    lines = [
        '# 🌍 সার্ভার IP দেশ অনুযায়ী লাইভ প্লেলিস্ট',
        '',
        f'মোট **{total}** লাইভ এন্ট্রি, **{len(summary)}**টি সার্ভার-দেশে। '
        'দেশ নির্ধারিত হয়েছে স্ট্রিম সার্ভারের IP থেকে (DB-IP, CC BY 4.0) — চ্যানেলের নাম থেকে নয়।',
        '',
        '| গ্রুপ | সার্ভার | এন্ট্রি | ফাইল |',
        '| --- | ---: | ---: | --- |',
    ]
    for item in summary:
        lines.append(
            f"| {item['group_title']} | {item['servers']} | {item['entries']} | `{item['file']}` |"
        )
    lines.extend([
        '',
        '## ব্যবহার',
        '',
        '- সব দেশ একসাথে: `COUNTRY_MASTER.m3u` (বাংলাদেশ প্রথমে, তারপর বাংলা বর্ণানুক্রম)।',
        '- শুধু একটি দেশ: সংশ্লিষ্ট `<CODE>_<COUNTRY>.m3u` ফাইল।',
        '- প্রতিটি ফাইলে `group-title="<পতাকা> <বাংলা নাম> (<কোড>)"`, `tvg-country` এবং `#EXTGRP` আছে।',
        '- `XX_UNKNOWN.m3u` থাকলে বোঝায় সেই সার্ভার IP-র দেশ সূচিতে পাওয়া যায়নি (প্রাইভেট/রিজার্ভড/DNS ব্যর্থ)।',
        '',
        '## অ্যাট্রিবিউশন',
        '',
        'IP Geolocation by [DB-IP](https://db-ip.com) — CC BY 4.0। বিস্তারিত `src/data/NOTICE.md`-এ।',
        '',
    ])
    (directory / 'README.md').write_text('\n'.join(lines), encoding='utf-8')


def _remove_stale(directory, keep):
    """Delete country playlists for countries that have no live channel today."""
    for path in directory.glob('*.m3u'):
        if path.name in ('COUNTRY_MASTER.m3u', 'README.md') or path.name in keep:
            continue
        if re.fullmatch(r'[A-Z]{2}_[A-Z0-9_]+\.m3u', path.name):
            path.unlink()
