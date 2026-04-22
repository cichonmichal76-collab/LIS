from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.runtime import create_temporary_database, ensure_runtime_schema
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def make_smoke_client(name: str):
    base_database_url = os.getenv("LIS_SMOKE_DATABASE_URL")
    cleanup = None
    if base_database_url:
        database_url, cleanup = create_temporary_database(base_database_url, name)
        settings = Settings(database_url=database_url, auto_create_schema=False)
    else:
        database_path = ROOT / "data" / f"{name}.sqlite3"
        if database_path.exists():
            database_path.unlink()
        database_url = f"sqlite:///{database_path.as_posix()}"
        settings = Settings(database_url=database_url, auto_create_schema=False)

    ensure_runtime_schema(settings.database_url)
    app = create_app(settings)

    try:
        with TestClient(app) as client:
            yield client
    finally:
        if cleanup is not None:
            cleanup()
