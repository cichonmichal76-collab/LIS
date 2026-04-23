from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4
from collections.abc import Callable

from sqlalchemy import create_engine, text
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.schema import CreateIndex, CreateTable

from app.db.base import Base

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_BOOTSTRAP_ROOT = ROOT / "db" / "runtime_bootstrap"
RUNTIME_BOOTSTRAP_MODES = {"runtime-sql", "metadata", "none"}


def detect_database_backend(database_url: str) -> str:
    if database_url.startswith("sqlite"):
        return "sqlite"
    if database_url.startswith("postgresql"):
        return "postgresql"
    return "unknown"


def connect_args_for_url(database_url: str) -> dict[str, object]:
    return {"check_same_thread": False} if detect_database_backend(database_url) == "sqlite" else {}


def create_runtime_engine(database_url: str) -> Engine:
    _ensure_sqlite_parent_directory(database_url)
    return create_engine(
        database_url,
        connect_args=connect_args_for_url(database_url),
        pool_pre_ping=True,
    )


def ping_database(database_url: str) -> None:
    engine = create_runtime_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    finally:
        engine.dispose()


def ensure_runtime_schema(database_url: str, *, mode: str = "runtime-sql") -> None:
    normalized_mode = normalize_runtime_bootstrap_mode(mode)
    if normalized_mode == "none":
        return
    if normalized_mode == "runtime-sql":
        apply_runtime_bootstrap(database_url)
        return
    if normalized_mode == "metadata":
        from app.db import models as _models  # noqa: F401

        engine = create_runtime_engine(database_url)
        try:
            Base.metadata.create_all(engine)
        finally:
            engine.dispose()
        return
    raise ValueError(f"Unsupported runtime bootstrap mode: {mode}")


def normalize_runtime_bootstrap_mode(mode: str | None) -> str:
    normalized = (mode or "runtime-sql").strip().lower()
    if normalized not in RUNTIME_BOOTSTRAP_MODES:
        raise ValueError(
            f"Unsupported runtime bootstrap mode: {mode}. "
            f"Expected one of {sorted(RUNTIME_BOOTSTRAP_MODES)}."
        )
    return normalized


def runtime_bootstrap_path(database_url: str) -> Path:
    backend = detect_database_backend(database_url)
    return runtime_bootstrap_path_for_backend(backend)


def runtime_bootstrap_path_for_backend(backend: str) -> Path:
    if backend == "sqlite":
        return RUNTIME_BOOTSTRAP_ROOT / "sqlite.sql"
    if backend == "postgresql":
        return RUNTIME_BOOTSTRAP_ROOT / "postgres.sql"
    raise ValueError(f"Unsupported database backend for runtime bootstrap: {backend}")


def render_runtime_bootstrap_sql(backend: str) -> str:
    from app.db import models as _models  # noqa: F401

    if backend == "sqlite":
        dialect = sqlite.dialect()
    elif backend == "postgresql":
        dialect = postgresql.dialect()
    else:
        raise ValueError(f"Unsupported database backend for runtime bootstrap rendering: {backend}")

    statements: list[str] = [
        f"-- Generated runtime bootstrap for {backend}.",
        "-- Source of truth: app/db/models.py",
        "",
    ]
    for table in Base.metadata.sorted_tables:
        statements.append(str(CreateTable(table, if_not_exists=True).compile(dialect=dialect)).strip() + ";")
        for index in sorted(table.indexes, key=lambda item: item.name or ""):
            statements.append(str(CreateIndex(index, if_not_exists=True).compile(dialect=dialect)).strip() + ";")
        statements.append("")
    return "\n".join(statements).rstrip() + "\n"


def write_runtime_bootstrap_sql(backend: str) -> Path:
    target = runtime_bootstrap_path_for_backend(backend)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_runtime_bootstrap_sql(backend), encoding="utf-8")
    return target


def apply_runtime_bootstrap(database_url: str) -> Path:
    path = runtime_bootstrap_path(database_url)
    if not path.exists():
        raise FileNotFoundError(
            f"Runtime bootstrap SQL was not found for {database_url}. Expected {path}."
        )
    backend = detect_database_backend(database_url)
    if backend == "sqlite":
        _apply_sqlite_migrations(database_url, [path])
    elif backend == "postgresql":
        _apply_postgres_migrations(database_url, [path])
    else:
        raise ValueError(f"Unsupported database backend for runtime bootstrap: {database_url}")
    return path


def apply_sql_migrations(database_url: str) -> list[Path]:
    backend = detect_database_backend(database_url)
    if backend not in {"sqlite", "postgresql"}:
        raise ValueError(f"Unsupported database backend for migrations: {database_url}")

    migration_dir = ROOT / "db" / "migrations" / ("sqlite" if backend == "sqlite" else "postgres")
    migration_files = sorted(migration_dir.glob("*.sql"))
    if not migration_files:
        raise FileNotFoundError(f"No migration files found in {migration_dir}")

    if backend == "sqlite":
        _apply_sqlite_migrations(database_url, migration_files)
    else:
        _apply_postgres_migrations(database_url, migration_files)
    return migration_files


def reset_database(database_url: str) -> None:
    backend = detect_database_backend(database_url)
    if backend == "sqlite":
        _reset_sqlite_database(database_url)
        return
    if backend == "postgresql":
        _reset_postgres_database(database_url)
        return
    raise ValueError(f"Unsupported database backend for reset: {database_url}")


def create_temporary_database(base_url: str, name_hint: str) -> tuple[str, Callable[[], None]]:
    backend = detect_database_backend(base_url)
    if backend == "sqlite":
        base_path = ROOT / "data"
        base_path.mkdir(parents=True, exist_ok=True)
        file_name = f"{_slugify(name_hint)}-{uuid4().hex[:8]}.sqlite3"
        database_path = base_path / file_name
        database_url = f"sqlite:///{database_path.as_posix()}"

        def cleanup() -> None:
            if database_path.exists():
                database_path.unlink()

        return database_url, cleanup

    if backend == "postgresql":
        return _create_temporary_postgres_database(base_url, name_hint)

    raise ValueError(f"Unsupported database backend for temporary database: {base_url}")


def _apply_sqlite_migrations(database_url: str, migration_files: list[Path]) -> None:
    engine = create_runtime_engine(database_url)
    try:
        raw_connection = engine.raw_connection()
        try:
            cursor = raw_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
            for migration_file in migration_files:
                raw_connection.executescript(migration_file.read_text(encoding="utf-8"))
            raw_connection.commit()
        finally:
            raw_connection.close()
    finally:
        engine.dispose()


def _apply_postgres_migrations(database_url: str, migration_files: list[Path]) -> None:
    engine = create_runtime_engine(database_url)
    try:
        with engine.begin() as connection:
            for migration_file in migration_files:
                connection.exec_driver_sql(migration_file.read_text(encoding="utf-8"))
    finally:
        engine.dispose()


def _reset_sqlite_database(database_url: str) -> None:
    if database_url.startswith("sqlite:///"):
        database_path = Path(database_url.removeprefix("sqlite:///"))
        if database_path.exists():
            database_path.unlink()
        return

    engine = create_runtime_engine(database_url)
    try:
        raw_connection = engine.raw_connection()
        try:
            cursor = raw_connection.cursor()
            tables = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            for (table_name,) in tables:
                cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            raw_connection.commit()
        finally:
            raw_connection.close()
    finally:
        engine.dispose()


def _reset_postgres_database(database_url: str) -> None:
    engine = create_runtime_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql("DROP SCHEMA IF EXISTS public CASCADE")
            connection.exec_driver_sql("CREATE SCHEMA public")
    finally:
        engine.dispose()


def _create_temporary_postgres_database(base_url: str, name_hint: str) -> tuple[str, callable]:
    base = make_url(base_url)
    admin_database = "postgres"
    admin_url = base.set(database=admin_database)
    database_name = f"{_slugify(name_hint)}_{uuid4().hex[:8]}"
    test_url = base.set(database=database_name)

    admin_engine = create_runtime_engine(admin_url.render_as_string(hide_password=False))
    try:
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)')
            connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')
    finally:
        admin_engine.dispose()

    def cleanup() -> None:
        cleanup_engine = create_runtime_engine(admin_url.render_as_string(hide_password=False))
        try:
            with cleanup_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
                connection.exec_driver_sql(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)')
        finally:
            cleanup_engine.dispose()

    return test_url.render_as_string(hide_password=False), cleanup


def _ensure_sqlite_parent_directory(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    db_path = database_url.removeprefix("sqlite:///")
    if not db_path or db_path == ":memory:":
        return
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def _slugify(value: str) -> str:
    stem = Path(value).stem.lower()
    normalized = re.sub(r"[^a-z0-9_]+", "_", stem)
    return normalized.strip("_") or "lis_test"
