from __future__ import annotations

import argparse

from app.core.config import Settings
from app.db.runtime import (
    detect_database_backend,
    ensure_runtime_schema,
    normalize_runtime_bootstrap_mode,
    reset_database,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset the configured database.")
    parser.add_argument("--database-url", dest="database_url", default=None)
    parser.add_argument("--migrate", action="store_true", help="Apply checked-in migrations after reset.")
    parser.add_argument(
        "--mode",
        default=None,
        help="Runtime bootstrap mode used with --migrate: runtime-sql, metadata, or none.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    database_url = args.database_url or settings.database_url
    reset_database(database_url)
    backend = detect_database_backend(database_url)
    print(f"Reset database: {backend} -> {database_url}")

    if args.migrate:
        mode = normalize_runtime_bootstrap_mode(args.mode or settings.schema_bootstrap_mode)
        ensure_runtime_schema(database_url, mode=mode)
        print(f"Ensured runtime schema after reset using {mode}.")


if __name__ == "__main__":
    main()
