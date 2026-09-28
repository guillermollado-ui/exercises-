import ipaddress
import socket
from urllib.parse import urlparse

from .errors import BlockedURLError, InvalidURLError

ALLOWED_SCHEMES = {"http", "https"}


def resolve_hostname(hostname: str) -> list[str]:
    """Wraps socket.getaddrinfo so tests can monkeypatch DNS resolution."""
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise InvalidURLError(f"Could not resolve host: {hostname}") from exc
    return [info[4][0] for info in addr_infos]


def _is_blocked_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def ensure_safe_url(url: str) -> str:
    """Validates the URL's scheme and blocks requests to private/internal
    addresses. Returns the URL unchanged when it is safe to fetch."""
    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise InvalidURLError(
            f"URL scheme must be http or https, got: {parsed.scheme or 'none'}"
        )

    if not parsed.hostname:
        raise InvalidURLError("URL must include a hostname")

    hostname = parsed.hostname.lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise BlockedURLError("Requests to localhost are not allowed")

    resolved_ips = resolve_hostname(hostname)
    if not resolved_ips:
        raise InvalidURLError(f"Could not resolve host: {hostname}")

    for ip_str in resolved_ips:
        if _is_blocked_ip(ip_str):
            raise BlockedURLError(
                f"Requests to private/internal addresses are not allowed: {ip_str}"
            )

    return url
