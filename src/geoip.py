"""Resolve the country of a stream server IP, fully offline.

The index in ``src/data`` is a compact DB-IP IP-to-country table (see
``tools/build_country_index.py`` and ``src/data/NOTICE.md``). It is loaded
lazily, so a run that never resolves an address never pays for parsing it.

Hostnames are resolved through the system stub resolver; every candidate
address is looked up and the first known country wins. Anything that cannot be
resolved (DNS failure, private address, range missing from the index) is
reported as ``XX`` and grouped under "unknown server" instead of guessing.
"""

import gzip
import ipaddress
import socket
import threading
from bisect import bisect_right
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from countries import UNKNOWN_CODE, COUNTRIES

DATA_DIR = Path(__file__).resolve().parent / 'data'
INDEX_FILES = {4: 'ip2country-v4.tsv.gz', 6: 'ip2country-v6.tsv.gz'}

# RFC 1918 / loopback / link-local / CGNAT / multicast / reserved space. Public
# playlists should never point here, and DB-IP deliberately leaves it out.
_PRIVATE_NETWORKS = tuple(
    ipaddress.ip_network(network) for network in (
        '0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8',
        '169.254.0.0/16', '172.16.0.0/12', '192.0.0.0/24', '192.0.2.0/24',
        '192.168.0.0/16', '198.18.0.0/15', '198.51.100.0/24', '203.0.113.0/24',
        '224.0.0.0/4', '240.0.0.0/4', '::/128', '::1/128', '64:ff9b::/96',
        '100::/64', '2001:db8::/32', 'fc00::/7', 'fe80::/10', 'ff00::/8',
    )
)


class _RangeIndex:
    """Sorted start addresses plus the country of the range each one begins."""

    def __init__(self, path):
        self.path = path
        self._starts = None
        self._countries = None
        self._lock = threading.Lock()

    def load(self):
        if self._starts is not None:
            return self
        with self._lock:
            if self._starts is None:
                starts, countries = [], []
                with gzip.open(self.path, 'rt', encoding='utf-8') as source:
                    for line in source:
                        if not line or line[0] == '#':
                            continue
                        start, country = line.rstrip('\n').split('\t')
                        starts.append(int(start))
                        countries.append(country)
                self._starts, self._countries = starts, countries
        return self

    def lookup(self, address):
        if not self:
            return UNKNOWN_CODE
        position = bisect_right(self._starts, int(address)) - 1
        if position < 0:
            return UNKNOWN_CODE
        return self._countries[position]

    def __bool__(self):
        return bool(self._starts)


_INDEXES = {version: _RangeIndex(DATA_DIR / name) for version, name in INDEX_FILES.items()}
_WARNED = set()
_WARN_LOCK = threading.Lock()


def _warn_once(message):
    with _WARN_LOCK:
        if message in _WARNED:
            return
        _WARNED.add(message)
    print(message)


def is_private(address):
    # IPv4-mapped IPv6 (``::ffff:127.0.0.1``) is judged as the IPv4 address it carries.
    if getattr(address, 'ipv4_mapped', None) is not None:
        address = address.ipv4_mapped
    return any(address in network for network in _PRIVATE_NETWORKS if network.version == address.version)


def lookup_ip(value):
    """Return the ISO code for one IP address string, or ``XX``."""
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return UNKNOWN_CODE
    if is_private(address):
        return UNKNOWN_CODE
    address = getattr(address, 'ipv4_mapped', None) or address
    index = _INDEXES.get(address.version)
    if index is None or not index.path.exists():
        return UNKNOWN_CODE
    index.load()
    return index.lookup(address)


@lru_cache(maxsize=8192)
def resolve_host(host):
    """Return every address for a host, newest DNS answers first, or ()."""
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError, OSError):
        return ()
    addresses = []
    for family, _, _, _, sockaddr in infos:
        if family in (socket.AF_INET, socket.AF_INET6) and sockaddr and sockaddr[0] not in addresses:
            addresses.append(sockaddr[0])
    return tuple(addresses)


def host_of(url):
    """Return the lowercase hostname or IP literal of an HTTP(S) URL."""
    try:
        host = urlsplit(url).hostname
    except ValueError:
        return ''
    return (host or '').rstrip('.').lower()


def lookup_host(host):
    """Return ``(country_code, address_used)`` for a hostname or literal."""
    if not host:
        return UNKNOWN_CODE, ''
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        return lookup_ip(str(literal)), str(literal)

    addresses = resolve_host(host)
    if not addresses:
        _warn_once(f'⚠️  DNS lookup failed for {host}; counted as an unknown server')
        return UNKNOWN_CODE, ''
    for address in addresses:
        code = lookup_ip(address)
        if code != UNKNOWN_CODE:
            return code, address
    return UNKNOWN_CODE, addresses[0]


def code_is_known(code):
    return code == UNKNOWN_CODE or code in COUNTRIES
