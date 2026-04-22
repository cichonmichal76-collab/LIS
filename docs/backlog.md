# MVP Backlog

## Sprint 0

- ADR-001 system shape: core plus FHIR facade plus device gateway
- ADR-002 stack selection
- ADR-003 auth and RBAC strategy
- development environment
- CI or CD
- PostgreSQL environment
- logging and tracing

## Sprint 1

- master data tables
- users and roles
- append-only audit
- base dictionaries
- health endpoints

## Sprint 2

- `test_catalog`
- LOINC subset import
- UCUM dictionary
- reference intervals
- catalog CRUD

## Sprint 3

- `lis_order`
- `lis_order_item`
- order registration
- order search
- requisition number policy

## Sprint 4

- `specimen`
- `container`
- accessioning
- labels
- collect or receive or accept or reject
- trace view

## Sprint 5

- `task_work`
- work queues
- claim or start or complete or fail
- bench dashboard

## Sprint 6

- `observation`
- manual result entry
- reference range snapshot
- abnormal or critical flags
- technical verification

## Sprint 7

- `diagnostic_report`
- `diagnostic_report_version`
- PDF rendering
- medical authorization
- publish or amend or retract

## Sprint 8

- `raw_instrument_message`
- first device parser
- barcode or accession correlation
- retry or dead-letter handling
- basic inbound FHIR
