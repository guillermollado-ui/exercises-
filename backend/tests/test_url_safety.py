import pytest

from app.errors import BlockedURLError, InvalidURLError
from app.url_safety import ensure_safe_url


def test_blocks_disallowed_scheme():
    with pytest.raises(InvalidURLError):
        ensure_safe_url("ftp://example.com/file")


def test_blocks_url_without_scheme():
    with pytest.raises(InvalidURLError):
        ensure_safe_url("example.com/page")


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://127.0.0.1:8000/admin",
        "http://localhost:3000/",
        "http://10.0.0.5/internal",
        "http://192.168.1.10/",
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata endpoint
        "http://0.0.0.0/",
    ],
)
def test_blocks_private_and_loopback_addresses(url):
    with pytest.raises(BlockedURLError):
        ensure_safe_url(url)


def test_allows_public_address(monkeypatch):
    monkeypatch.setattr(
        "app.url_safety.resolve_hostname", lambda hostname: ["93.184.216.34"]
    )
    assert ensure_safe_url("https://example.com/") == "https://example.com/"


def test_blocks_when_hostname_resolves_to_private_ip(monkeypatch):
    """DNS rebinding style case: a normal-looking hostname resolving to a private IP."""
    monkeypatch.setattr(
        "app.url_safety.resolve_hostname", lambda hostname: ["10.1.2.3"]
    )
    with pytest.raises(BlockedURLError):
        ensure_safe_url("https://internal.example.com/")
