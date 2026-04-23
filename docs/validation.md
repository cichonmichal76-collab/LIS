# Validation

The current repository has been revalidated in this v11 step on:

- the local SQLite development path

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
.\\.venv\\Scripts\\python.exe scripts\\smoke_test_qc.py
.\.venv\Scripts\python.exe scripts\smoke_test_transport.py
.\.venv\Scripts\python.exe scripts\analyzer_runtime.py --once
.\.venv\Scripts\python.exe scripts\smoke_test_runtime.py
.\.venv\Scripts\python.exe scripts\smoke_test_matrix.py
.\.venv\Scripts\python.exe scripts\export_openapi.py
.\.venv\Scripts\python.exe scripts\migrate.py
@'
import sqlite3
from pathlib import Path

root = Path(r'C:/Users/cicho/OneDrive/Pulpit/LIS')
db_path = root / 'db' / 'validation_qc.sqlite3'
if db_path.exists():
    db_path.unlink()
conn = sqlite3.connect(db_path)
try:
    for rel in [
        'db/migrations/sqlite/0001_init.sql',
        'db/migrations/sqlite/002_autoverification_astm.sql',
        'db/migrations/sqlite/003_analyzer_transport.sql',
        'db/migrations/sqlite/004_analyzer_runtime_profile.sql',
        'db/migrations/sqlite/005_qc_engine.sql',
    ]:
        sql = (root / rel).read_text(encoding='utf-8')
        conn.executescript(sql)
    conn.commit()
finally:
    conn.close()
'@ | .\.venv\Scripts\python.exe -
```

## Current Result

- lint: OK
- compile: OK
- pytest: `23 passed`
- core smoke: OK
- FHIR smoke: OK
- integration smoke: OK
- autoverification smoke: OK
- ASTM smoke: OK
- QC smoke: OK
- analyzer transport smoke: OK
- analyzer runtime one-shot: OK
- analyzer runtime smoke: OK
- smoke matrix: OK
- OpenAPI export: OK
- runtime schema bootstrap: OK

## PostgreSQL E2E

The PostgreSQL Compose path remains available and documented in [PostgreSQL E2E](postgres-e2e.md).

For this v11 QC-and-autoverification step, the locally re-run validation in this environment was completed on:

- SQLite runtime
- full pytest
- full smoke matrix
- QC-specific smoke flow
- advanced autoverification rule coverage through pytest
- transport-specific smoke flow
- analyzer runtime flow

A Docker Compose rerun was not completed on 2026-04-23 because the Docker daemon was not running in
this environment.

## Checked-In SQL Migration Validation

The checked-in canonical SQLite migrations were also executed on a clean SQLite file in sequence:

- `db/migrations/sqlite/0001_init.sql`
- `db/migrations/sqlite/002_autoverification_astm.sql`
- `db/migrations/sqlite/003_analyzer_transport.sql`
- `db/migrations/sqlite/004_analyzer_runtime_profile.sql`
- `db/migrations/sqlite/005_qc_engine.sql`

Result: OK.

## Current Boundary

- runtime and smoke coverage are proven end-to-end on SQLite in this v11 step
- PostgreSQL E2E remains documented and available, but was not re-run in this environment on 2026-04-23 because Docker was unavailable
- canonical checked-in SQL migrations for PostgreSQL are present, but the runtime app still bootstraps its current operational schema from SQLAlchemy metadata
- analyzer transport sessions, framing, ACK/NAK, retry, and dispatch are covered, but physical TCP/serial analyzer I/O is still outside this validation step
- analyzer runtime worker is covered on the mock connector path, while real TCP and serial devices still require environment-specific validation
- production deployment hardening and broader multi-level clinical/QC rule coverage are still outside this validation step
