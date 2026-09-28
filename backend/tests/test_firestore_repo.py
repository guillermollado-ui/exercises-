from unittest.mock import MagicMock

from app import firestore_repo


def test_get_recent_analyses_queries_ordered_and_limited(monkeypatch):
    fake_doc_1 = MagicMock()
    fake_doc_1.id = "doc-1"
    fake_doc_1.to_dict.return_value = {"url": "https://example.com/a", "title": "A"}

    fake_doc_2 = MagicMock()
    fake_doc_2.id = "doc-2"
    fake_doc_2.to_dict.return_value = {"url": "https://example.com/b", "title": "B"}

    fake_query = MagicMock()
    fake_query.stream.return_value = [fake_doc_1, fake_doc_2]

    fake_collection = MagicMock()
    fake_collection.order_by.return_value.limit.return_value = fake_query

    fake_client = MagicMock()
    fake_client.collection.return_value = fake_collection

    monkeypatch.setattr(firestore_repo, "get_firestore_client", lambda: fake_client)

    results = firestore_repo.get_recent_analyses(limit=10)

    fake_client.collection.assert_called_once_with("analyses")
    order_args, _ = fake_collection.order_by.call_args
    assert order_args[0] == "analyzed_at"
    fake_collection.order_by.return_value.limit.assert_called_once_with(10)

    assert results == [
        {"id": "doc-1", "url": "https://example.com/a", "title": "A"},
        {"id": "doc-2", "url": "https://example.com/b", "title": "B"},
    ]


def test_save_analysis_writes_document(monkeypatch):
    fake_doc_ref = MagicMock()
    fake_doc_ref.id = "new-doc-id"

    fake_collection = MagicMock()
    fake_collection.add.return_value = (MagicMock(), fake_doc_ref)

    fake_client = MagicMock()
    fake_client.collection.return_value = fake_collection

    monkeypatch.setattr(firestore_repo, "get_firestore_client", lambda: fake_client)

    result = firestore_repo.save_analysis(
        "https://example.com", {"title": "Example", "word_count": 5}
    )

    fake_client.collection.assert_called_once_with("analyses")
    saved_doc = fake_collection.add.call_args[0][0]
    assert saved_doc["url"] == "https://example.com"
    assert saved_doc["title"] == "Example"
    assert "analyzed_at" in saved_doc

    assert result["id"] == "new-doc-id"
    assert result["url"] == "https://example.com"
