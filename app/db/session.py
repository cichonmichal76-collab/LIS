from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.runtime import ensure_runtime_schema, normalize_runtime_bootstrap_mode


class DatabaseSessionManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._ensure_parent_directory(database_url)
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
        )

    def create_schema(self, *, mode: str = "runtime-sql") -> None:
        ensure_runtime_schema(self.database_url, mode=normalize_runtime_bootstrap_mode(mode))

    def dispose(self) -> None:
        self.engine.dispose()

    @staticmethod
    def _ensure_parent_directory(database_url: str) -> None:
        if not database_url.startswith("sqlite:///"):
            return
        db_path = database_url.removeprefix("sqlite:///")
        if not db_path or db_path == ":memory:":
            return
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
