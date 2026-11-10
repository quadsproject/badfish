"""Outbound HTTP/SOCKS proxy support for badfish HTTP clients."""

from urllib.parse import urlsplit

PROXY_SCHEMES = ("http", "https", "socks4", "socks4a", "socks5", "socks5h")


class ProxyError(Exception):
    pass


def redact_proxy(proxy):
    """Proxy URL with any userinfo credentials stripped, for error messages."""
    scheme, sep, rest = proxy.partition("//")
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


def build_connector(proxy):
    """Build an aiohttp proxy connector for a validated proxy URL, or None.

    SOCKS uses the aiohttp-socks package. socks5h/socks4a resolve DNS on the
    proxy side, socks5/socks4 resolve locally (same semantics as PySocks in
    quads-client and mozzo).
    """
    if not proxy:
        return None
    parse_proxy(proxy)
    try:
        from aiohttp_socks import ProxyConnector
    except ImportError:
        raise ProxyError(
            "The 'aiohttp-socks' package is required for proxy support. " "Install it (pip install aiohttp-socks)."
        )
    parts = urlsplit(proxy)
    normalized = f"{parts.scheme}://{parts.netloc}"
    rdns = None
    if parts.scheme in ("socks4", "socks5"):
        rdns = False
    elif parts.scheme == "socks4a":
        normalized = f"socks4://{parts.netloc}"
        rdns = True
    elif parts.scheme == "socks5h":
        normalized = f"socks5://{parts.netloc}"
        rdns = True
    return ProxyConnector.from_url(normalized, rdns=rdns)
