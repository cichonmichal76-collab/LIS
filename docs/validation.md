# Validation

The current repository has been locally validated on the SQLite development path.

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
.\.venv\Scripts\python.exe scripts\export_openapi.py
.\.venv\Scripts\python.exe scripts\migrate.py
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
- OpenAPI export: OK
- runtime schema bootstrap: OK

## Checked-In SQL Migration Validation

The checked-in canonical SQLite migrations were also executed on a clean SQLite file in sequence:

- `db/migrations/sqlite/0001_init.sql`
- `db/migrations/sqlite/002_autoverification_astm.sql`

Result: OK.

## Current Boundary

- the PostgreSQL path is prepared in code, checked-in SQL, dependencies, and `docker-compose`
- full end-to-end runtime execution against a live PostgreSQL container was not run in this validation step
