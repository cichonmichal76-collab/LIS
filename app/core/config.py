from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "LIS Core API"
APP_VERSION = "0.7.1"


def _default_database_url() -> str:
    db_path = Path(__file__).resolve().parents[2] / "db" / "lis.sqlite3"
    return f"sqlite:///{db_path.as_posix()}"


@dataclass(frozen=True)
class Settings:
    database_url: str
    auto_create_schema: bool = True
    jwt_secret: str = "dev-secret-change-me-please-replace-32b"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv("LIS_DATABASE_URL", _default_database_url()),
            auto_create_schema=os.getenv("LIS_AUTO_CREATE_SCHEMA", "true").lower()
            in {"1", "true", "yes", "on"},
            jwt_secret=os.getenv("LIS_JWT_SECRET", "dev-secret-change-me-please-replace-32b"),
            jwt_algorithm=os.getenv("LIS_JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("LIS_ACCESS_TOKEN_EXPIRE_MINUTES", "480")),
        )
