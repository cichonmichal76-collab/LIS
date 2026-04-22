# LIS Core Starter

Starter repo for a greenfield LIS v1 built as a modular monolith with:

- `PostgreSQL` as the canonical transactional store
- `FastAPI` as the internal REST layer and future FHIR facade host
- `OpenAPI` as the checked-in API contract
- append-only audit and provenance records from day one

## What is included

- `db/migrations/0001_lis_core.sql`
  First-pass schema for master data, orders, specimens, tasks, results, reports, audit, and provenance.
- `openapi/lis-internal-v1.yaml`
  Internal API contract for the first operational slice: `orders`, `specimens`, and `tasks`.
- `app/`
  Minimal FastAPI service skeleton with route placeholders aligned to the contract.
- `docs/architecture.md`
  Architectural decisions and mapping from relational core to FHIR resources.

## Quick start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
uvicorn app.main:app --reload
```

## Current status

This repo is intentionally at the "real starter pack" stage:

- schema is defined,
- API contract is defined,
- routes are wired,
- business logic and persistence are not implemented yet.

That gives a clean baseline for building the next slices without redesigning the core model.

## Suggested next milestones

1. Add database access and migrations runner integration.
2. Implement `orders -> accessioning -> specimen lifecycle`.
3. Add `observations` and `diagnostic_report` workflows.
4. Introduce a FHIR facade for `ServiceRequest`, `Specimen`, `Task`, `Observation`, and `DiagnosticReport`.

