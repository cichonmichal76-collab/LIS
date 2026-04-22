# LIS v1 Architecture

## Baseline decisions

- Architecture style: modular monolith first, integration adapters second.
- Canonical model: relational core shaped to map cleanly to FHIR diagnostics resources.
- Integration boundaries:
  - internal REST API for operational workflows,
  - future FHIR facade for interoperability,
  - separate device gateway for analyzer protocols and raw payload handling.

## Why this shape

The highest risk in LIS is domain traceability, not service decomposition. A single transactional core makes it easier to preserve consistency across:

- order intake,
- specimen lifecycle,
- execution tasks,
- result provenance,
- report versioning,
- audit evidence.

## Core modules

- master data
- test catalog and terminology
- order management
- specimen management
- work management
- result engine
- reporting
- integration layer
- quality and compliance

## Persistence model

The starter migration creates the following important entities:

- `lis_order`, `lis_order_item`
- `specimen`, `container`, `specimen_event`
- `task_work`
- `raw_instrument_message`
- `observation`, `observation_link`
- `diagnostic_report`, `diagnostic_report_version`, `report_observation`
- `audit_event_log`
- `provenance_record`

Supporting entities are included for master data and terminology:

- `patient`, `encounter_case`
- `organization`, `location`
- `practitioner`, `practitioner_role`, `app_user`
- `device`
- `test_catalog`, `test_catalog_member`, `reference_interval`

## Status design

Business workflow state and standards-facing resource state are intentionally separate.

- Internal workflow lives in tables such as `lis_order.status`, `specimen.status`, and `task_work.status`.
- FHIR-facing state should be mapped, not stored as the only source of truth.

That prevents a common LIS failure mode where operational and interoperability semantics get mixed into one brittle status field.

## FHIR mapping plan

- `lis_order_item` -> `ServiceRequest`
- `lis_order.requisition_no` -> `ServiceRequest.requisition`
- `specimen` -> `Specimen`
- `task_work` -> `Task`
- `observation` -> `Observation`
- `observation_link` -> `Observation.hasMember`, `Observation.derivedFrom`, `Observation.triggeredBy`
- `diagnostic_report` + active version -> `DiagnosticReport`
- `audit_event_log` -> `AuditEvent`
- `provenance_record` -> `Provenance`

`container` remains a richer internal model than base FHIR `Specimen.container`, because LIS traceability usually needs recursive physical storage relationships.

## Device integration

Instrument connectivity belongs in a dedicated gateway. The core schema already reserves:

- `raw_instrument_message` for immutable payload storage,
- `parser_version` for reproducibility,
- correlation fields for `accession_no` and `specimen_barcode`.

That design keeps low-level transport concerns out of the domain core while preserving traceability.

## Contract-first execution

The repository is intentionally contract-first:

- SQL schema defines the transactional backbone.
- OpenAPI defines the internal workflow surface.
- FastAPI skeleton keeps the service bootable while implementation catches up.

## Immediate next implementation slice

1. Persist `orders`.
2. Create accessioning for `specimens`.
3. Implement `tasks` for routing and queue ownership.
4. Add append-only audit write hooks on every state transition.
