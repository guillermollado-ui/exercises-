import os
from functools import lru_cache


class Settings:
    def __init__(self) -> None:
        self.frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
        self.firebase_credentials_path: str = os.getenv(
            "FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json"
        )
        self.request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
