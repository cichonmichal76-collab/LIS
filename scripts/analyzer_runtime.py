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
    parser.add_argument("--worker-id", type=str, default=None, help="Override the runtime worker identifier.")
    parser.add_argument(
        "--lease-timeout-seconds",
        type=int,
        default=15,
        help="Lease heartbeat timeout for owned transport sessions.",
    )
    parser.add_argument(
        "--retry-backoff-seconds",
        type=int,
        default=5,
        help="Base backoff delay applied after runtime transport errors.",
    )
    parser.add_argument(
        "--retry-backoff-max-seconds",
        type=int,
        default=60,
        help="Maximum backoff delay applied after runtime transport errors.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    settings = Settings.from_env()
    db = DatabaseSessionManager(settings.database_url)
    worker = AnalyzerRuntimeWorker(
        db.session_factory,
        worker_id=args.worker_id,
        lease_timeout_seconds=args.lease_timeout_seconds,
        retry_backoff_seconds=args.retry_backoff_seconds,
        retry_backoff_max_seconds=args.retry_backoff_max_seconds,
    )
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
