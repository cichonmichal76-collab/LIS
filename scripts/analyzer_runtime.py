from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from uuid import UUID

from app.core.config import Settings
from app.db.session import DatabaseSessionManager
from app.services.analyzer_runtime import AnalyzerRuntimeWorker


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the LIS analyzer transport runtime worker.")
    parser.add_argument("--once", action="store_true", help="Run a single worker cycle and exit.")
    parser.add_argument("--sleep-seconds", type=float, default=1.0, help="Pause between worker cycles.")
    parser.add_argument("--max-iterations", type=int, default=None, help="Optional loop limit.")
    parser.add_argument("--device-id", type=str, default=None, help="Restrict runtime to one device.")
    parser.add_argument("--profile-id", type=str, default=None, help="Restrict runtime to one transport profile.")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    settings = Settings.from_env()
    db = DatabaseSessionManager(settings.database_url)
    worker = AnalyzerRuntimeWorker(db.session_factory)
    try:
        if args.once:
            stats = worker.run_once(
                device_id=UUID(args.device_id) if args.device_id else None,
                profile_id=UUID(args.profile_id) if args.profile_id else None,
            )
            print(json.dumps(asdict(stats), indent=2, sort_keys=True))
            return

        worker.run_forever(
            sleep_seconds=args.sleep_seconds,
            max_iterations=args.max_iterations,
            device_id=UUID(args.device_id) if args.device_id else None,
            profile_id=UUID(args.profile_id) if args.profile_id else None,
        )
    finally:
        worker.close()
        db.dispose()


if __name__ == "__main__":
    main()
