from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from .errors import FetchConnectionError, FetchTimeoutError, NonHTMLContentError
from .url_safety import ensure_safe_url

USER_AGENT = "seo-analyzer/1.0"
MAX_REDIRECTS = 5


def fetch_html(url: str, timeout_seconds: float) -> str:
    """Fetches url, following redirects manually so every hop — not just the
    original URL — is re-validated by ensure_safe_url. httpx's built-in
    follow_redirects=True would fetch a redirect target without ever
    checking it, letting a public URL that 302s to a private IP bypass the
    SSRF guard entirely."""
    current_url = ensure_safe_url(url)

    for _ in range(MAX_REDIRECTS + 1):
        try:
            response = httpx.get(
                current_url,
                timeout=timeout_seconds,
                follow_redirects=False,
                headers={"User-Agent": USER_AGENT},
            )
        except httpx.TimeoutException as exc:
            raise FetchTimeoutError(f"Request to {url} timed out") from exc
        except httpx.HTTPError as exc:
            raise FetchConnectionError(f"Could not fetch {url}: {exc}") from exc

        if response.is_redirect:
            location = response.headers.get("location")
            if not location:
                raise FetchConnectionError(
                    f"Redirect from {current_url} had no Location header"
                )
            current_url = ensure_safe_url(urljoin(current_url, location))
            continue

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise FetchConnectionError(f"Could not fetch {url}: {exc}") from exc

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type.lower():
            raise NonHTMLContentError(
                f"Expected an HTML page, got content-type: {content_type or 'unknown'}"
            )

        return response.text

    raise FetchConnectionError(f"Too many redirects while fetching {url}")


def parse_seo_fields(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    title = title_text or None

    meta_tag = soup.find("meta", attrs={"name": lambda v: bool(v) and v.lower() == "description"})
    meta_content = meta_tag.get("content", "").strip() if meta_tag else ""
    meta_description = meta_content or None

    h1 = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2 = [h.get_text(strip=True) for h in soup.find_all("h2")]

    body_text = soup.get_text(separator=" ", strip=True)
    word_count = len(body_text.split())

    return {
        "title": title,
        "meta_description": meta_description,
        "h1": h1,
        "h2": h2,
        "word_count": word_count,
    }


def analyze_url(url: str, timeout_seconds: float) -> dict:
    html = fetch_html(url, timeout_seconds)
    return parse_seo_fields(html)
