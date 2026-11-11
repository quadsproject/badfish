"""Outbound HTTP/SOCKS proxy support for badfish HTTP clients."""

import base64
from urllib.parse import unquote, urlsplit

PROXY_SCHEMES = ("http", "https", "socks4", "socks4a", "socks5", "socks5h")
SOCKS_SCHEMES = ("socks4", "socks4a", "socks5", "socks5h")


class ProxyError(Exception):
    pass


def redact_proxy(proxy):
    """Proxy URL with any userinfo credentials stripped, for error messages."""
    scheme, sep, rest = proxy.partition("//")
    if "@" in scheme:
        scheme = scheme.rsplit("@", 1)[-1]
    authority = rest if sep else proxy
    host = authority.rsplit("@", 1)[-1]
    return f"{scheme}//{host}" if sep else host


def parse_proxy(proxy):
    """Validate a proxy URL, raising ProxyError with a redacted message."""
    if not proxy:
        return None
    if any(c.isspace() or ord(c) < 32 for c in proxy):
        raise ProxyError(f"Invalid proxy URL: {redact_proxy(proxy)}")
    try:
        parts = urlsplit(proxy)
    except ValueError:
        raise ProxyError(f"Invalid proxy URL: {redact_proxy(proxy)}")
    if parts.scheme not in PROXY_SCHEMES:
        supported = ", ".join(s for s in PROXY_SCHEMES if s != "https")
        raise ProxyError(
            f"Unsupported proxy scheme '{parts.scheme}' in {redact_proxy(proxy)}. "
            f"Use one of: {supported} (e.g. socks5h://127.0.0.1:1080)"
        )
    if parts.scheme == "https":
        raise ProxyError("The 'https' proxy scheme (TLS to the proxy) is not supported; " "use http:// or socks5h://")
    try:
        port = parts.port
    except ValueError:
        raise ProxyError(f"Proxy URL has an invalid port: {redact_proxy(proxy)}")
    if not parts.hostname or not port:
        raise ProxyError(
            "Proxy URL must include a host and port (e.g. socks5h://127.0.0.1:1080): " f"{redact_proxy(proxy)}"
        )
    return proxy


def request_proxy_url(proxy):
    """Redacted proxy URL for aiohttp's native request-level ``proxy=`` kwarg.

    Plain ``http://`` proxies are handled natively by aiohttp and do not need
    aiohttp-socks; userinfo is stripped (credentials travel in the
    Proxy-Authorization header, see proxy_auth_header, so they never appear in
    aiohttp error messages). SOCKS and direct connections return None here and
    use build_connector() instead.
    """
    if not proxy:
        return None
    if urlsplit(proxy).scheme in SOCKS_SCHEMES:
        return None
    return redact_proxy(proxy)


def proxy_auth_header(proxy):
    """``Proxy-Authorization`` header value from an http proxy URL's userinfo, or None."""
    if not proxy or urlsplit(proxy).scheme != "http":
        return None
    parts = urlsplit(proxy)
    if parts.username is None:
        return None
    username = unquote(parts.username)
    password = unquote(parts.password or "")
    token = base64.b64encode(f"{username}:{password}".encode("latin-1")).decode("ascii")
    return f"Basic {token}"


def build_connector(proxy):
    """Build an aiohttp-socks ProxyConnector for SOCKS proxies, or None.

    Plain ``http://`` proxies return None: aiohttp handles them natively via
    the request-level ``proxy=`` kwarg (see request_proxy_url), so
    aiohttp-socks is only required for SOCKS. socks5h/socks4a resolve DNS on
    the proxy side, socks5/socks4 resolve locally (same semantics as PySocks
    in quads-client and mozzo).
    """
    if not proxy:
        return None
    parse_proxy(proxy)
    scheme = urlsplit(proxy).scheme
    if scheme not in SOCKS_SCHEMES:
        return None
    try:
        from aiohttp_socks import ProxyConnector
    except ImportError:
        raise ProxyError(
            "The 'aiohttp-socks' package is required for SOCKS proxies. " "Install it (pip install aiohttp-socks)."
        )
    parts = urlsplit(proxy)
    normalized = f"{scheme}://{parts.netloc}"
    rdns = None
    if scheme in ("socks4", "socks5"):
        rdns = False
    elif scheme == "socks4a":
        normalized = f"socks4://{parts.netloc}"
        rdns = True
    elif scheme == "socks5h":
        normalized = f"socks5://{parts.netloc}"
        rdns = True
    return ProxyConnector.from_url(normalized, rdns=rdns)
