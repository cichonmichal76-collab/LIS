# PostgreSQL E2E

This document describes how to run the full LIS backend validation path on PostgreSQL through Docker Compose.

## Goal

The PostgreSQL E2E path verifies that:

- the app starts from a dynamic `LIS_DATABASE_URL`
- `/health` performs a real database ping
- the runtime schema can be bootstrapped from checked-in runtime SQL
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
2. `python scripts/export_runtime_bootstrap.py --check`
3. `python scripts/migrate.py --database-url .../${POSTGRES_DB} --mode runtime-sql`
4. `python scripts/validate_sql_artifacts.py`
5. `pytest -q`
6. `python scripts/smoke_test_matrix.py`

## Start only the API on PostgreSQL

If you want to run the API instead of the full validation flow:

```powershell
docker compose up --build
```

The `api` service executes:

1. `python scripts/wait_for_db.py`
2. `python scripts/migrate.py`
3. `uvicorn app.main:app --host 0.0.0.0 --port 8000`

The `analyzer-runtime` service executes:

1. `python scripts/wait_for_db.py`
2. `python scripts/migrate.py`
3. `python scripts/analyzer_runtime.py`

## What to verify after startup

- `GET /health`
  It should return `status=ok` and `database_status=ok`
- `test-runner` logs
  They should show a green `pytest` run and `Smoke test matrix OK`

## Current repository result

The PostgreSQL E2E path is part of the supported project workflow and is now also reflected in:

- [docker-compose.yml](C:/Users/cicho/OneDrive/Pulpit/LIS/docker-compose.yml)
- [.github/workflows/ci.yml](C:/Users/cicho/OneDrive/Pulpit/LIS/.github/workflows/ci.yml)
- [docs/runtime-bootstrap.md](C:/Users/cicho/OneDrive/Pulpit/LIS/docs/runtime-bootstrap.md)

Previously confirmed baseline result on a live PostgreSQL container:

- `docker compose run --rm test-runner`
- `pytest -q` -> `14 passed`
- `smoke_test_matrix.py` -> OK

For the v13 PostgreSQL-first step on 2026-04-23, a local Docker rerun was still not possible in this
environment because the Docker daemon was unavailable.

## Known boundary

- the runtime schema is now bootstrapped from checked-in runtime SQL snapshots, but it is still a snapshot-based path rather than a full revisioned runtime migration framework
- the current local smoke matrix and pytest path were re-run on SQLite in this environment, but not re-run here on a live PostgreSQL daemon on 2026-04-23
- real analyzer runtime validation still depends on environment-specific TCP/serial access
