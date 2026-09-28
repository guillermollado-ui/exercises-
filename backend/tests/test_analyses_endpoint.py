def test_get_analyses_returns_last_10_newest_first(client, monkeypatch):
    fake_records = [
        {
            "id": f"doc-{i}",
            "url": f"https://example.com/page-{i}",
            "title": f"Page {i}",
            "meta_description": None,
            "h1": [],
            "h2": [],
            "word_count": 10,
            "analyzed_at": None,
        }
        for i in range(10, 0, -1)  # already newest-first, as Firestore would return
    ]
    monkeypatch.setattr("app.main.get_recent_analyses", lambda limit=10: fake_records)

    response = client.get("/api/analyses")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 10
    assert [item["url"] for item in body] == [r["url"] for r in fake_records]


def test_get_analyses_empty(client):
    response = client.get("/api/analyses")
    assert response.status_code == 200
    assert response.json() == []
