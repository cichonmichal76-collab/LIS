from __future__ import annotations

import argparse
from pathlib import Path

from app.db.runtime import render_runtime_bootstrap_sql, write_runtime_bootstrap_sql


def main() -> None:
    parser = argparse.ArgumentParser(description="Export checked-in runtime bootstrap SQL snapshots.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that checked-in runtime bootstrap SQL matches the current SQLAlchemy models.",
    )
    args = parser.parse_args()

    targets = {
        "sqlite": Path("db/runtime_bootstrap/sqlite.sql"),
        "postgresql": Path("db/runtime_bootstrap/postgres.sql"),
    }

    if args.check:
        mismatches: list[str] = []
        for backend, path in targets.items():
            expected = render_runtime_bootstrap_sql(backend)
            actual = path.read_text(encoding="utf-8") if path.exists() else ""
            if actual != expected:
                mismatches.append(str(path))
        if mismatches:
            raise SystemExit(
                "Runtime bootstrap SQL is out of date. Regenerate with "
                f"`python scripts/export_runtime_bootstrap.py`. Mismatched files: {', '.join(mismatches)}"
            )
        print("Runtime bootstrap SQL is up to date.")
        return

    exported_paths = [
        write_runtime_bootstrap_sql("sqlite"),
        write_runtime_bootstrap_sql("postgresql"),
    ]
    for path in exported_paths:
        print(f"Exported runtime bootstrap SQL to {path}")


if __name__ == "__main__":
    main()
