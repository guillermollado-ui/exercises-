import datetime
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore

from .config import get_settings

COLLECTION_NAME = "analyses"


@lru_cache
def get_firestore_client():
    settings = get_settings()
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()


def save_analysis(url: str, result: dict) -> dict:
    client = get_firestore_client()
    document = {
        "url": url,
        **result,
        "analyzed_at": datetime.datetime.now(datetime.timezone.utc),
    }
    _, doc_ref = client.collection(COLLECTION_NAME).add(document)
    return {"id": doc_ref.id, **document}


def get_recent_analyses(limit: int = 10) -> list[dict]:
    client = get_firestore_client()
    query = (
        client.collection(COLLECTION_NAME)
        .order_by("analyzed_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    results = []
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results
