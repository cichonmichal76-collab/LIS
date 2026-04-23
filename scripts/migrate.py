from __future__ import annotations

import argparse

from app.core.config import Settings
from app.db.runtime import detect_database_backend, ensure_runtime_schema, normalize_runtime_bootstrap_mode


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the configured runtime schema.")
    parser.add_argument("--database-url", dest="database_url", default=None)
    parser.add_argument(
        "--mode",
        default=None,
        help="Runtime bootstrap mode: runtime-sql, metadata, or none.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    database_url = args.database_url or settings.database_url
    mode = normalize_runtime_bootstrap_mode(args.mode or settings.schema_bootstrap_mode)
    try:
        ensure_runtime_schema(database_url, mode=mode)
    except Exception as exc:
        backend = detect_database_backend(database_url)
        if mode == "runtime-sql":
            raise SystemExit(
                "Runtime SQL bootstrap failed. If this is an older local database, reset it first with "
                "`python scripts/reset_db.py --migrate` or point migrate.py at a fresh database URL. "
                f"Backend={backend}. Original error: {exc}"
            ) from exc
        raise
    backend = detect_database_backend(database_url)
    print(f"Ensured runtime schema on {backend} using {mode}: {database_url}")


if __name__ == "__main__":
    main()
