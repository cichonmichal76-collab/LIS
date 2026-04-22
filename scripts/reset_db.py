from __future__ import annotations

import argparse

from app.core.config import Settings
from app.db.runtime import detect_database_backend, ensure_runtime_schema, reset_database


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset the configured database.")
    parser.add_argument("--database-url", dest="database_url", default=None)
    parser.add_argument("--migrate", action="store_true", help="Apply checked-in migrations after reset.")
    args = parser.parse_args()

    database_url = args.database_url or Settings.from_env().database_url
    reset_database(database_url)
    backend = detect_database_backend(database_url)
    print(f"Reset database: {backend} -> {database_url}")

    if args.migrate:
        ensure_runtime_schema(database_url)
        print("Ensured runtime schema after reset.")


if __name__ == "__main__":
    main()
