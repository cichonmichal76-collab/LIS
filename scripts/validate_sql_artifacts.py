from __future__ import annotations

import sqlite3
from pathlib import Path

from app.db.runtime import apply_runtime_bootstrap

ROOT = Path(__file__).resolve().parents[1]


def _execute_canonical_sqlite_migrations(target_path: Path) -> None:
    conn = sqlite3.connect(target_path)
    try:
        for rel in [
            "db/migrations/sqlite/0001_init.sql",
            "db/migrations/sqlite/002_autoverification_astm.sql",
            "db/migrations/sqlite/003_analyzer_transport.sql",
            "db/migrations/sqlite/004_analyzer_runtime_profile.sql",
            "db/migrations/sqlite/005_qc_engine.sql",
            "db/migrations/sqlite/006_analyzer_runtime_hardening.sql",
        ]:
            sql = (ROOT / rel).read_text(encoding="utf-8")
            conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def main() -> None:
    runtime_path = ROOT / "data" / "validate_runtime_bootstrap.sqlite3"
    canonical_path = ROOT / "data" / "validate_canonical_sqlite.sqlite3"
    runtime_path.parent.mkdir(parents=True, exist_ok=True)

    for path in [runtime_path, canonical_path]:
        if path.exists():
            path.unlink()

    try:
        apply_runtime_bootstrap(f"sqlite:///{runtime_path.as_posix()}")
        _execute_canonical_sqlite_migrations(canonical_path)

        print("Runtime bootstrap SQL validation OK")
        print("Canonical SQLite migration validation OK")
    finally:
        for path in [runtime_path, canonical_path]:
            if path.exists():
                path.unlink()


if __name__ == "__main__":
    main()
