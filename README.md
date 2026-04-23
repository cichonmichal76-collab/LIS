# LIS Core Starter

Starter repo for a greenfield LIS v1 built as a modular monolith with:

- `PostgreSQL` as the canonical transactional store
- `FastAPI` as the internal REST layer and FHIR facade host
- `OpenAPI` as the checked-in API contract
- append-only audit and provenance records from day one

## What is included

- `db/migrations/0001_lis_core.sql`
  First-pass schema for master data, orders, specimens, tasks, results, reports, audit, and provenance.
- `db/schema.sql`
  Canonical target PostgreSQL schema imported from the starter pack and kept as the design target.
- `db/migrations/postgres/*.sql` and `db/migrations/sqlite/*.sql`
  Checked-in SQL bootstrap files for the canonical design on PostgreSQL and SQLite,
  including v10 additions for device mappings, interface logs, autoverification,
  QC engine, ASTM-style support, analyzer transport, analyzer runtime,
  and v12 runtime lease/backoff hardening.
- `db/runtime_bootstrap/*.sql`
  Checked-in runtime bootstrap SQL generated from `app/db/models.py` and used by the
  v13 `runtime-sql` bootstrap path for the current operational schema.
- `openapi/lis-internal-v1.yaml`
  Generated internal API contract for the current implemented slices:
  `auth`, `patients`, `test-catalog`, `orders`, `specimens`, `tasks`,
  `observations`, `reports`, `audit`, `provenance`, `devices`, `qc`,
  `integrations`, and `analyzer-transport`.
- `openapi/lis-target-v1.yaml`
  Target API contract for the broader LIS MVP, including `observations`, `reports`, `audit`, and device ingest.
- `app/`
  FastAPI service with working persistence, JWT auth, RBAC, HL7 v2 starter adapter,
  device gateway, autoverification, QC engine, ASTM-style drivers, analyzer transport
  sessions, a hardened background analyzer runtime, and a read/search FHIR R4 facade.
- `scripts/`
  Runtime helpers for schema bootstrap, OpenAPI export, demo seed data, REST smoke flow,
  FHIR smoke flow, integration smoke flow, autoverification smoke flow, ASTM smoke flow,
  analyzer transport smoke flow, analyzer runtime smoke flow, runtime bootstrap export,
  SQL artifact validation, database wait/reset helpers, and a smoke matrix runner.
- `Dockerfile` and `docker-compose.yml`
  Container path for the API, analyzer runtime, and PostgreSQL, including a `test-runner`
  service for end-to-end validation.
- `.env.example` and `Makefile`
  Ready-to-use local env template and common developer commands for migrate/test/smoke/docker flows.
- `.github/workflows/ci.yml`
  CI for SQLite and PostgreSQL validation, including pytest, smoke matrix, and runtime bootstrap checks.
- `docs/`
  Architecture, workflow, FHIR mapping, repo structure, backlog, and current-vs-target alignment notes.

## Quick start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
uvicorn app.main:app --reload
```

Supporting scripts:

```powershell
python scripts/migrate.py
python scripts/export_runtime_bootstrap.py
python scripts/export_runtime_bootstrap.py --check
python scripts/seed_demo_data.py
python scripts/export_openapi.py
python scripts/validate_sql_artifacts.py
python scripts/wait_for_db.py
python scripts/reset_db.py --migrate
python scripts/smoke_test.py
python scripts/smoke_test_fhir.py
python scripts/smoke_test_integration.py
python scripts/smoke_test_autoverification.py
python scripts/smoke_test_astm.py
python scripts/smoke_test_qc.py
python scripts/smoke_test_transport.py
python scripts/analyzer_runtime.py --once
python scripts/smoke_test_runtime.py
python scripts/smoke_test_matrix.py
```

PostgreSQL path:

```powershell
Copy-Item .env.example .env
docker compose up --build
docker compose run --rm test-runner
```

Optional runtime config:

- `LIS_DATABASE_URL`
  Defaults to a local SQLite file at `db/lis.sqlite3` for fast development.
- `LIS_AUTO_CREATE_SCHEMA`
  Defaults to `true` and bootstraps the runtime schema on app startup.
- `LIS_SCHEMA_BOOTSTRAP_MODE`
  Defaults to `runtime-sql`. Supported values: `runtime-sql`, `metadata`, `none`.
- `LIS_TEST_DATABASE_URL`
  Optional base database URL used by pytest to create isolated temporary test databases.
- `LIS_SMOKE_DATABASE_URL`
  Optional base database URL used by smoke tests to create isolated temporary smoke databases.
- `LIS_JWT_SECRET`
  Secret used for bearer token signing.
- `LIS_JWT_ALGORITHM`
  Defaults to `HS256`.
- `LIS_ACCESS_TOKEN_EXPIRE_MINUTES`
  Defaults to `480`.
- `LIS_ANALYZER_RUNTIME_SLEEP_SECONDS`
  Default pause between analyzer runtime worker cycles in Docker Compose.

## Current status

This repo now includes a working persistence slice for:

- JWT auth and RBAC with `admin`, `accessioner`, `technician`, `pathologist`, and `viewer`,
- `patients` and `test-catalog`,
- `orders`, `specimens`, `tasks`, `observations`, and `reports`,
- `devices`, `device mappings`, `interface messages`, and `raw instrument messages`,
- rule-based autoverification with evaluate/apply and append-only run history,
- richer autoverification conditions for reference intervals, interpretation codes, and delta recency,
- QC materials, lots, rules, runs, results, and QC gate enforcement for observation/report release,
- placeholder report PDF rendering under `/api/v1/reports/{report_id}/pdf`,
- append-only `audit` and `provenance`,
- HL7 v2 starter interoperability for inbound/outbound `OML^O33` and `ORU^R01`,
- device gateway worklists and analyzer result ingest with traceability to `raw_message_id`,
- ASTM-style worklist export and result import with optional autoverification chaining,
- analyzer transport profiles, sessions, outbound queue, ASTM framing,
  `ENQ`/`ACK`/`NAK`/`EOT`, retry handling, frame logs, and dispatch into ASTM import,
- analyzer runtime worker with `mock`, `tcp-client`, and `serial` connector modes,
  lease ownership, retry backoff, runtime overview API,
  and a dedicated Docker Compose service for background transport processing,
- runtime bootstrap SQL generated from ORM metadata and used by `scripts/migrate.py`,
- SQLite and PostgreSQL CI coverage through GitHub Actions,
- FHIR R4 `read` and `search-type` for `Patient`, `ServiceRequest`, `Specimen`,
  `Task`, `Observation`, `DiagnosticReport`, `AuditEvent`, and `Provenance`,
- dynamic `DATABASE_URL` runtime selection with real database ping in `/health`,
- explicit runtime schema bootstrap modes with `runtime-sql` as the preferred checked-in path,
- SQLite local validation, plus a documented PostgreSQL end-to-end path through
  `docker compose run --rm test-runner` when Docker is available.

That gives a clean baseline for building the next slices without redesigning the core model.

## Current Vs Target

This repository now carries two complementary layers:

- Current implemented slice
  `app/`, `tests/`, `db/migrations/0001_lis_core.sql`, and `openapi/lis-internal-v1.yaml`
- Canonical target design
  `db/schema.sql`, `openapi/lis-target-v1.yaml`, and the planning docs under `docs/`

The current implementation is intentionally narrower than the target design. It already proves the workflow for:

- bootstrap admin, login, and bearer-authenticated access,
- patient and test catalog master data,
- order creation and item management,
- specimen accessioning and lifecycle,
- work task creation and state transitions,
- manual observation entry and technical verification,
- report generation, authorization, and amendment,
- placeholder PDF retrieval per report version,
- append-only audit writes and provenance tracking on those transitions,
- device registry, incoming test code mappings, worklists, and analyzer ingest,
- autoverification rules, evaluation, apply flow, and manual-review task creation,
- HL7 v2 order/result import-export for `OML^O33` and `ORU^R01`,
- ASTM-style worklist export and result ingest,
- analyzer transport sessions and ASTM-style framed message handling,
- background analyzer runtime with connector abstraction and smoke coverage,
- FHIR `CapabilityStatement` plus read/search facade under `/fhir/R4`.

The target design extends that baseline to:

- deeper PostgreSQL-first alignment with canonical target tables,
- vendor-specific device drivers and richer interface protocols,
- richer connection recovery, deeper replay/dead-letter handling, and production hardening for the analyzer runtime,
- deeper QC coverage such as richer Westgard/trend rules and operational QC scheduling,
- richer FHIR interoperability such as write interactions, subscriptions, and profiles.

## Suggested next milestones

1. Add deeper replay/dead-letter handling, reconnect policies, and runtime metrics export.
2. Add multi-level QC, richer trend rules, and deeper clinical/autoverification context.
3. Add richer user and practitioner linkage beyond starter RBAC.
4. Add richer FHIR features such as writes, subscriptions, and profile validation.

## Design Docs

- [Architecture](docs/architecture.md)
- [Workflow](docs/workflow.md)
- [FHIR Facade](docs/fhir-facade.md)
- [Dependency Tree](docs/dependency-tree.md)
- [HL7 v2 Adapter](docs/hl7-v2-adapter.md)
- [Device Gateway](docs/device-gateway.md)
- [Autoverification Engine](docs/autoverification-engine.md)
- [QC Engine](docs/qc-engine.md)
- [ASTM Driver Layer](docs/astm-driver-layer.md)
- [Analyzer Transport](docs/analyzer-transport.md)
- [Analyzer Runtime](docs/analyzer-runtime.md)
- [PostgreSQL E2E](docs/postgres-e2e.md)
- [Validation](docs/validation.md)
- [FHIR Mapping](docs/fhir-mapping.md)
- [Repo Structure](docs/repo-structure.md)
- [Backlog](docs/backlog.md)
- [Alignment](docs/alignment.md)
