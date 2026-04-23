# Validation

The current repository has been revalidated in this v13 step on:

- the local SQLite development path

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check app tests scripts
.\.venv\Scripts\python.exe -m compileall app scripts tests
.\.venv\Scripts\python.exe scripts\export_runtime_bootstrap.py --check
.\.venv\Scripts\python.exe scripts\validate_sql_artifacts.py
.\.venv\Scripts\pytest.exe -q
.\.venv\Scripts\python.exe scripts\smoke_test_matrix.py
.\.venv\Scripts\python.exe scripts\analyzer_runtime.py --once
.\.venv\Scripts\python.exe scripts\export_openapi.py
if (Test-Path data\v13_runtime_migrate.sqlite3) { Remove-Item data\v13_runtime_migrate.sqlite3 -Force }
.\.venv\Scripts\python.exe scripts\migrate.py --database-url sqlite:///C:/Users/cicho/OneDrive/Pulpit/LIS/data/v13_runtime_migrate.sqlite3 --mode runtime-sql
```

## Current Result

- lint: OK
- compile: OK
- runtime bootstrap SQL snapshot check: OK
- checked-in SQL artifact validation: OK
- pytest: `26 passed`
- core smoke: OK
- FHIR smoke: OK
- integration smoke: OK
- autoverification smoke: OK
- ASTM smoke: OK
- QC smoke: OK
- analyzer transport smoke: OK
- analyzer runtime smoke: OK
- smoke matrix: OK
- analyzer runtime one-shot: OK
- OpenAPI export: OK
- runtime schema bootstrap (`runtime-sql`): OK

## PostgreSQL E2E

The PostgreSQL Compose path remains available and documented in [PostgreSQL E2E](postgres-e2e.md).

For this v13 PostgreSQL-first and CI step, the locally re-run validation in this environment was completed on:

- SQLite runtime
- full pytest
- full smoke matrix
- runtime SQL snapshot verification
- checked-in SQL artifact verification

A Docker Compose rerun was not completed on 2026-04-23 because the Docker daemon was not running in
this environment.

## Checked-In SQL Validation

Two SQL layers were verified in this step:

- runtime bootstrap SQL under `db/runtime_bootstrap/*.sql`
- canonical SQLite target migrations under `db/migrations/sqlite/*.sql`

Result: OK.

## Current Boundary

- runtime and smoke coverage are proven end-to-end on SQLite in this v13 step
- PostgreSQL E2E remains documented and wired into Compose and CI, but was not re-run in this local environment on 2026-04-23 because Docker was unavailable
- runtime schema bootstrap is now checked in and validated, but it is still snapshot-based rather than a full revisioned runtime migration framework
- existing older local databases may still require `reset_db.py --migrate` because `runtime-sql` is a bootstrap snapshot, not a full in-place upgrader
- canonical target migrations and runtime bootstrap SQL now coexist intentionally; they solve different problems and still require discipline to keep aligned
- analyzer runtime worker is covered on the mock connector path, while real TCP and serial devices still require environment-specific validation
- production deployment hardening, replay/dead-letter flow, and exported runtime metrics are still outside this validation step
