"""Read M3U entries without changing names, metadata, order, or duplicates."""

from urllib.parse import urlsplit


def read_preamble(file_path):
    """Preserve the playlist header and global comments before the first entry."""
    preamble = []
    with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as source:
        for raw_line in source:
            line = raw_line.strip()
            if line.startswith('#EXTINF'):
                break
            if line.startswith('#'):
                preamble.append(line)
    headers = [line for line in preamble if line.startswith('#EXTM3U')]
    comments = [line for line in preamble if not line.startswith('#EXTM3U')]
    return [headers[0] if headers else '#EXTM3U', *comments]


def parse_m3u(file_path, strict=False):
    """Read HTTP(S) entries and retain the original EXTINF and directives.

    Strict mode rejects incomplete or unsupported entries rather than silently
    skipping them. Identical names and URLs remain separate source entries.
    """
    channels = []
    extinf = None
    extinf_line = None
    directives = []
    with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as source:
        for line_number, raw_line in enumerate(source, start=1):
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith('#EXTINF'):
                if strict and extinf is not None:
                    raise ValueError(f'Entry at line {extinf_line} is missing a URL')
                extinf, extinf_line, directives = line, line_number, []
            elif extinf is not None and line.startswith('#'):
                directives.append(line)
            elif extinf is not None:
                try:
                    parsed = urlsplit(line)
                    has_control_chars = any(ord(char) < 32 or ord(char) == 127 for char in line)
                    supported = parsed.scheme.lower() in ('http', 'https') and bool(parsed.netloc) and not has_control_chars
                except ValueError:
                    supported = False
                if not supported and strict:
                    raise ValueError(f'Entry at line {extinf_line} has an invalid or unsupported HTTP(S) URL')
                if supported:
                    channels.append({'extinf': extinf, 'directives': directives, 'url': line})
                extinf, extinf_line, directives = None, None, []
            elif strict and not line.startswith('#'):
                raise ValueError(f'URL at line {line_number} has no preceding #EXTINF')
    if strict and extinf is not None:
        raise ValueError(f'Entry at line {extinf_line} is missing a URL')
    return channels
