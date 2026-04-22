from __future__ import annotations

import argparse
import time

from app.core.config import Settings
from app.db.runtime import detect_database_backend, ping_database


def main() -> None:
    parser = argparse.ArgumentParser(description="Wait until the configured database is reachable.")
    parser.add_argument("--database-url", dest="database_url", default=None)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--interval", type=int, default=2)
    args = parser.parse_args()

    database_url = args.database_url or Settings.from_env().database_url
    started_at = time.monotonic()
    last_error: Exception | None = None

    while time.monotonic() - started_at < args.timeout:
        try:
            ping_database(database_url)
            backend = detect_database_backend(database_url)
            print(f"Database is ready: {backend} -> {database_url}")
            return
        except Exception as exc:
            last_error = exc
            time.sleep(args.interval)

    raise SystemExit(f"Database was not ready after {args.timeout}s: {last_error}")


if __name__ == "__main__":
    main()
