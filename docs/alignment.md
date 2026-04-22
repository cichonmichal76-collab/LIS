# Current Vs Target Alignment

## What Already Matches

- Relational LIS core centered on orders, specimens, tasks, observations, reports, audit, and provenance
- FHIR-shaped domain model around `ServiceRequest`, `Specimen`, `Observation`, `DiagnosticReport`, `AuditEvent`, and `Provenance`
- Separate device gateway concept instead of embedding protocol logic into the transactional core
- Explicit local container tracking because base FHIR `Specimen` is not enough for recursive storage traceability
- Local plus LOINC plus UCUM terminology strategy
- Versioned reports instead of in-place overwrites
- Append-only audit intent from day one

## What Is Already Implemented

- Working FastAPI persistence slice for `orders`, `specimens`, and `tasks`
- State transitions and basic guardrails for those workflows
- Runtime audit writes on those transitions
- API tests covering the first workflow slice

## What Exists Only As Target Design Today

- Separate `storage_location` table
- Observation workflow and verification endpoints
- Diagnostic report generation, authorization, and amendment endpoints
- Audit search endpoint
- Device ingest endpoint and raw payload handling in the API layer
- PostgreSQL-first runtime alignment
- FHIR facade resources and mappings in executable form

## Known Drift To Resolve

- Runtime development currently defaults to SQLite, while the target design assumes PostgreSQL as canonical storage
- The implemented API is narrower than the target API and uses server-assigned workflow details in a few places where the target contract is more explicit
- The current internal API still exposes an `order item hold` workflow, which is not yet formalized in the target contract and should either be adopted into the target or removed later

## Recommended Next Alignment Steps

1. Normalize status and relation naming before expanding observations and reports.
2. Add PostgreSQL-backed migrations runner and converge runtime models onto migration-managed tables.
3. Implement observations and reports against the target contract.
4. Add device ingest and audit search after the observation or report slice is stable.
