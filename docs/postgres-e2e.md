# PostgreSQL E2E

This document describes how to run the full LIS backend validation path on PostgreSQL through Docker Compose.

## Goal

The PostgreSQL E2E path verifies that:

- the app starts from a dynamic `LIS_DATABASE_URL`
- `/health` performs a real database ping
- the runtime schema can be bootstrapped inside the container
- `pytest` passes on PostgreSQL
- smoke tests pass on PostgreSQL

## Prerequisites

- Docker Desktop or another compatible Docker runtime
- `docker compose`
- the repo files `Dockerfile`, `docker-compose.yml`, and `.env.example`

## Prepare the environment

Create a local `.env` file:

```powershell
Copy-Item .env.example .env
```

The defaults from `.env.example` are sufficient for a local developer run.

## Full validation run

Build the test image:

```powershell
docker compose build test-runner
```

Run the full PostgreSQL validation flow:

```powershell
docker compose run --rm test-runner
```

The `test-runner` service executes:

1. `python scripts/wait_for_db.py --database-url .../postgres`
2. `pytest -q`
3. `python scripts/smoke_test_matrix.py`

## Start only the API on PostgreSQL

If you want to run the API instead of the full validation flow:

```powershell
docker compose up --build
```

The `api` service executes:

1. `python scripts/wait_for_db.py`
2. `python scripts/migrate.py`
3. `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## What to verify after startup

- `GET /health`
  It should return `status=ok` and `database_status=ok`
- `test-runner` logs
  They should show a green `pytest` run and `Smoke test matrix OK`

## Current repository result

The PostgreSQL E2E path has been validated on a live PostgreSQL container through:

```powershell
docker compose run --rm test-runner
```

Result:

- `pytest -q` -> `14 passed`
- `smoke_test_matrix.py` -> OK

## Known boundary

- the runtime app still bootstraps its current operational schema through SQLAlchemy metadata
- checked-in SQL migrations remain important project artifacts, but they are not yet the sole runtime migration mechanism
- this flow does not yet cover QC, advanced delta checks, or full analyzer transport with ACK/retry/framing
