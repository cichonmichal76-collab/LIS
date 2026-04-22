# Validation

The current repository has been validated on both:

- the local SQLite development path
- the Docker Compose PostgreSQL path

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check app tests scripts
.\.venv\Scripts\python.exe -m compileall app scripts tests
.\.venv\Scripts\pytest.exe -q
.\.venv\Scripts\python.exe scripts\smoke_test.py
.\.venv\Scripts\python.exe scripts\smoke_test_fhir.py
.\.venv\Scripts\python.exe scripts\smoke_test_integration.py
.\.venv\Scripts\python.exe scripts\smoke_test_autoverification.py
.\.venv\Scripts\python.exe scripts\smoke_test_astm.py
.\.venv\Scripts\python.exe scripts\smoke_test_matrix.py
.\.venv\Scripts\python.exe scripts\export_openapi.py
.\.venv\Scripts\python.exe scripts\migrate.py
docker compose build test-runner
docker compose run --rm test-runner
```

## Current Result

- lint: OK
- compile: OK
- pytest: `14 passed`
- core smoke: OK
- FHIR smoke: OK
- integration smoke: OK
- autoverification smoke: OK
- ASTM smoke: OK
- smoke matrix: OK
- OpenAPI export: OK
- runtime schema bootstrap: OK
- PostgreSQL Compose E2E: OK
  - `wait_for_db.py`: OK
  - `pytest -q`: `14 passed`
  - `smoke_test_matrix.py`: OK

## Checked-In SQL Migration Validation

The checked-in canonical SQLite migrations were also executed on a clean SQLite file in sequence:

- `db/migrations/sqlite/0001_init.sql`
- `db/migrations/sqlite/002_autoverification_astm.sql`

Result: OK.

## Current Boundary

- runtime and smoke coverage are proven end-to-end on PostgreSQL through Docker Compose
- canonical checked-in SQL migrations for PostgreSQL are present, but the runtime app still bootstraps its current operational schema from SQLAlchemy metadata
- production deployment hardening, QC, advanced analyzer transport, and broader clinical rule coverage are still outside this validation step
