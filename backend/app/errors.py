class AnalyzerError(Exception):
    """Base class for errors raised while analyzing a URL."""


class InvalidURLError(AnalyzerError):
    """The URL is malformed, uses a disallowed scheme, or cannot be resolved."""


class BlockedURLError(AnalyzerError):
    """The URL resolves to a private/loopback/internal address (SSRF guard)."""


class FetchTimeoutError(AnalyzerError):
    """The page did not respond within the configured timeout."""


class FetchConnectionError(AnalyzerError):
    """The page could not be reached (DNS, connection refused, etc.)."""


class NonHTMLContentError(AnalyzerError):
    """The response was not an HTML document."""
