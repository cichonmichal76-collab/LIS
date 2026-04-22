from __future__ import annotations

from app.core.config import Settings
from app.db.session import DatabaseSessionManager


def main() -> None:
    settings = Settings.from_env()
    db = DatabaseSessionManager(settings.database_url)
    try:
        db.create_schema()
    finally:
        db.dispose()
    print(f"Schema ensured for {settings.database_url}")


if __name__ == "__main__":
    main()
