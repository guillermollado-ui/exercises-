import httpx
import pytest

from conftest import load_fixture


def _mock_get(body: str, content_type: str = "text/html; charset=utf-8", status_code: int = 200):
    def fake_get(url, timeout=None, follow_redirects=None, headers=None):
        return httpx.Response(
            status_code,
            text=body,
            headers={"content-type": content_type},
            request=httpx.Request("GET", url),
        )

    return fake_get


@pytest.fixture
def public_dns(monkeypatch):
    """Domain-name URLs need a mocked DNS resolution so tests never hit the network."""
    monkeypatch.setattr("app.url_safety.resolve_hostname", lambda hostname: ["93.184.216.34"])


def test_analyze_success(client, monkeypatch, public_dns, no_firestore):
    html = load_fixture("full_page.html")
    monkeypatch.setattr(httpx, "get", _mock_get(html))

    response = client.post("/api/analyze", json={"url": "https://example.com/coffee"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Best Coffee Beans Online | Acme Roasters"
    assert body["meta_description"] == (
        "Shop freshly roasted coffee beans delivered to your door every week."
    )
    assert body["h1"] == ["Best Coffee Beans Online"]
    assert body["h2"] == ["Single Origin Selection", "Subscription Plans"]
    assert body["word_count"] > 0
    assert "console.log" not in " ".join(body["h1"] + body["h2"])

    assert len(no_firestore) == 1
    assert no_firestore[0]["url"] == "https://example.com/coffee"


def test_analyze_missing_title_and_meta(client, monkeypatch, public_dns, no_firestore):
    html = load_fixture("missing_meta.html")
    monkeypatch.setattr(httpx, "get", _mock_get(html))

    response = client.post("/api/analyze", json={"url": "https://example.com/no-meta"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] is None
    assert body["meta_description"] is None
    assert body["h1"] == []
    assert body["h2"] == []
    assert body["word_count"] > 0


def test_analyze_invalid_url_scheme(client):
    response = client.post("/api/analyze", json={"url": "ftp://example.com/file"})
    assert response.status_code == 400
    assert "scheme" in response.json()["detail"].lower()


def test_analyze_timeout(client, monkeypatch, public_dns):
    def fake_get(url, timeout=None, follow_redirects=None, headers=None):
        raise httpx.TimeoutException("timed out", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    response = client.post("/api/analyze", json={"url": "https://example.com/slow"})
    assert response.status_code == 504


def test_analyze_connection_error(client, monkeypatch, public_dns):
    def fake_get(url, timeout=None, follow_redirects=None, headers=None):
        raise httpx.ConnectError("connection refused", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    response = client.post("/api/analyze", json={"url": "https://example.com/down"})
    assert response.status_code == 502


def test_analyze_non_html_response(client, monkeypatch, public_dns):
    body_text = load_fixture("not_html.txt")
    monkeypatch.setattr(httpx, "get", _mock_get(body_text, content_type="application/json"))

    response = client.post("/api/analyze", json={"url": "https://example.com/data.json"})
    assert response.status_code == 400


def test_analyze_blocked_private_ip(client):
    """Uses a literal private IP so no DNS mocking is needed — fully offline."""
    response = client.post("/api/analyze", json={"url": "http://192.168.1.50/"})
    assert response.status_code == 400
    assert "private" in response.json()["detail"].lower() or "internal" in response.json()["detail"].lower()


def test_analyze_blocks_ssrf_via_redirect(client, monkeypatch):
    """A public URL that 302s to a private IP must be blocked, not silently
    followed. Uses IP literals throughout so it needs no DNS mocking."""

    def fake_get(url, timeout=None, follow_redirects=None, headers=None):
        assert url == "http://93.184.216.34/start", "must not follow the redirect target"
        return httpx.Response(
            302,
            headers={"location": "http://192.168.1.50/"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    response = client.post("/api/analyze", json={"url": "http://93.184.216.34/start"})
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "private" in detail or "internal" in detail


def test_analyze_follows_safe_redirect(client, monkeypatch, no_firestore):
    """Legitimate redirects between two safe addresses still work end to end."""
    html = load_fixture("full_page.html")
    calls = []

    def fake_get(url, timeout=None, follow_redirects=None, headers=None):
        calls.append(url)
        if url == "http://93.184.216.34/old-page":
            return httpx.Response(
                301,
                headers={"location": "http://93.184.216.34/new-page"},
                request=httpx.Request("GET", url),
            )
        return httpx.Response(
            200,
            text=html,
            headers={"content-type": "text/html; charset=utf-8"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    response = client.post("/api/analyze", json={"url": "http://93.184.216.34/old-page"})

    assert response.status_code == 200
    assert calls == ["http://93.184.216.34/old-page", "http://93.184.216.34/new-page"]


def test_analyze_too_many_redirects(client, monkeypatch):
    def fake_get(url, timeout=None, follow_redirects=None, headers=None):
        return httpx.Response(
            302,
            headers={"location": "http://93.184.216.34/next"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    response = client.post("/api/analyze", json={"url": "http://93.184.216.34/start"})
    assert response.status_code == 502
