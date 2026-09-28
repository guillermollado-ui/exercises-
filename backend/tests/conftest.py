import pathlib
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def no_firestore(monkeypatch):
    """Every test runs against a fake Firestore layer; no test should hit the network."""
    saved_calls = []

    def fake_save(url, result):
        record = {"id": "fake-id", "url": url, **result, "analyzed_at": None}
        saved_calls.append(record)
        return record

    monkeypatch.setattr("app.main.save_analysis", fake_save)
    monkeypatch.setattr("app.main.get_recent_analyses", lambda limit=10: [])
    return saved_calls
