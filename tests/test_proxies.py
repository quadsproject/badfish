import builtins

import pytest

from badfish.helpers.proxies import (
    ProxyError,
    build_connector,
    parse_proxy,
    proxy_auth_header,
    redact_proxy,
    request_proxy_url,
)
from badfish.helpers.parser import parse_arguments

try:
    from aiohttp_socks import ProxyConnector
    from python_socks import ProxyType
except ImportError:
    ProxyConnector = ProxyType = None

requires_socks = pytest.mark.skipif(ProxyConnector is None, reason="aiohttp-socks not installed")


def test_parse_arguments_accepts_proxy():
    args = parse_arguments(["-H", "host", "-u", "u", "-p", "p", "--proxy", "socks5h://127.0.0.1:1080"])
    assert args["proxy"] == "socks5h://127.0.0.1:1080"


def test_parse_arguments_empty_proxy_returns_none():
    args = parse_arguments(["-H", "host", "-u", "u", "-p", "p", "--proxy", ""])
    assert args["proxy"] is None


def test_parse_arguments_rejects_invalid_proxy():
    with pytest.raises(SystemExit):
        parse_arguments(["-H", "host", "-u", "u", "-p", "p", "--proxy", "ftp://127.0.0.1:1080"])


def test_parse_proxy_empty_returns_none():
    assert parse_proxy("") is None
    assert parse_proxy(None) is None


def test_parse_proxy_valid():
    assert parse_proxy("socks5h://127.0.0.1:1080") == "socks5h://127.0.0.1:1080"


def test_parse_proxy_unsupported_scheme():
    with pytest.raises(ProxyError, match="Unsupported proxy scheme 'ftp'"):
        parse_proxy("ftp://127.0.0.1:1080")


def test_parse_proxy_https_rejected():
    with pytest.raises(ProxyError, match="https.*not supported"):
        parse_proxy("https://127.0.0.1:1080")


def test_parse_proxy_missing_host():
    with pytest.raises(ProxyError, match="must include a host and port"):
        parse_proxy("socks5h://:1080")


def test_parse_proxy_missing_port():
    with pytest.raises(ProxyError, match="must include a host and port"):
        parse_proxy("socks5h://127.0.0.1")


def test_parse_proxy_invalid_port():
    with pytest.raises(ProxyError, match="invalid port"):
        parse_proxy("socks5h://127.0.0.1:notaport")


def test_parse_proxy_port_out_of_range():
    with pytest.raises(ProxyError, match="invalid port"):
        parse_proxy("socks5h://127.0.0.1:99999")


def test_parse_proxy_rejects_whitespace():
    with pytest.raises(ProxyError, match="Invalid proxy URL"):
        parse_proxy("http://user:pa ss@h:1080")


def test_parse_proxy_malformed_ipv6():
    with pytest.raises(ProxyError, match="Invalid proxy URL"):
        parse_proxy("socks5h://user:secret@[::1")


def test_parse_proxy_redacts_userinfo():
    with pytest.raises(ProxyError) as exc:
        parse_proxy("http://user:secret@:3128")
    assert "secret" not in str(exc.value)


def test_parse_proxy_redacts_userinfo_before_scheme():
    with pytest.raises(ProxyError) as exc:
        parse_proxy("user:secret@http://host:3128")
    assert "secret" not in str(exc.value)
    assert "Unsupported proxy scheme" in str(exc.value)


def test_redact_proxy_strips_userinfo():
    assert redact_proxy("http://user:secret@10.0.0.1:3128") == "http://10.0.0.1:3128"
    assert redact_proxy("socks5h://user:p@ss@127.0.0.1:1080") == "socks5h://127.0.0.1:1080"
    assert redact_proxy("127.0.0.1:1080") == "127.0.0.1:1080"
    assert redact_proxy("user:secret@http://10.0.0.1:3128") == "http://10.0.0.1:3128"


def test_parse_proxy_accepts_uppercase_scheme():
    assert parse_proxy("SOCKS5H://127.0.0.1:1080") == "SOCKS5H://127.0.0.1:1080"


def test_build_connector_empty_returns_none():
    assert build_connector("") is None
    assert build_connector(None) is None


def test_build_connector_socks_requires_aiohttp_socks(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "aiohttp_socks":
            raise ImportError("No module named 'aiohttp_socks'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ProxyError, match="required for SOCKS proxies"):
        build_connector("socks5://127.0.0.1:1080")


def test_request_proxy_url_http_only():
    assert request_proxy_url("http://10.0.0.1:3128") == "http://10.0.0.1:3128"
    assert request_proxy_url("http://user:pass@10.0.0.1:3128") == "http://10.0.0.1:3128"
    assert request_proxy_url("socks5h://127.0.0.1:1080") is None
    assert request_proxy_url("") is None
    assert request_proxy_url(None) is None


def test_proxy_auth_header():
    assert proxy_auth_header("http://10.0.0.1:3128") is None
    assert proxy_auth_header("http://user:pass@10.0.0.1:3128") == "Basic dXNlcjpwYXNz"
    assert proxy_auth_header("http://user%40x:p%40ss@10.0.0.1:3128") == "Basic dXNlckB4OnBAc3M="
    assert proxy_auth_header("socks5h://user:pass@127.0.0.1:1080") is None
    assert proxy_auth_header("") is None
    assert proxy_auth_header(None) is None


def test_build_connector_http_returns_none():
    assert build_connector("http://10.0.0.1:3128") is None


def test_build_connector_http_needs_no_aiohttp_socks(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "aiohttp_socks":
            raise ImportError("No module named 'aiohttp_socks'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert build_connector("http://10.0.0.1:3128") is None


@requires_socks
async def test_build_connector_socks5_resolves_locally():
    conn = build_connector("socks5://127.0.0.1:1080")
    assert conn._proxy_type == ProxyType.SOCKS5
    assert conn._rdns is False


@requires_socks
async def test_build_connector_socks5h_resolves_remotely():
    conn = build_connector("socks5h://127.0.0.1:1080")
    assert conn._proxy_type == ProxyType.SOCKS5
    assert conn._rdns is True


@requires_socks
async def test_build_connector_socks4_resolves_locally():
    conn = build_connector("socks4://127.0.0.1:1080")
    assert conn._proxy_type == ProxyType.SOCKS4
    assert conn._rdns is False


@requires_socks
async def test_build_connector_socks4a_resolves_remotely():
    conn = build_connector("socks4a://127.0.0.1:1080")
    assert conn._proxy_type == ProxyType.SOCKS4
    assert conn._rdns is True


@requires_socks
async def test_build_connector_keeps_userinfo():
    conn = build_connector("socks5://user:pass@127.0.0.1:1080")
    assert conn._proxy_host == "127.0.0.1"
    assert conn._proxy_username == "user"
    assert conn._proxy_password == "pass"
