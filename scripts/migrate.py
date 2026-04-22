from __future__ import annotations

from app.core.config import Settings
from app.db.runtime import detect_database_backend, ensure_runtime_schema


def main() -> None:
    settings = Settings.from_env()
    ensure_runtime_schema(settings.database_url)
    backend = detect_database_backend(settings.database_url)
    print(f"Ensured runtime schema on {backend}: {settings.database_url}")


if __name__ == "__main__":
    main()
