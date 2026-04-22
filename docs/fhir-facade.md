# FHIR Facade

The current LIS repo exposes a read/search FHIR R4 facade under `/fhir/R4`.

Implemented interactions:

- `GET /fhir/R4/metadata`
- `read` and `search-type` for:
  - `Patient`
  - `ServiceRequest`
  - `Specimen`
  - `Task`
  - `Observation`
  - `DiagnosticReport`
  - `AuditEvent`
  - `Provenance`

The facade is intentionally read-only in this stage. It maps the transactional LIS core
to FHIR-shaped resources without introducing write interactions or full FHIR persistence.

Current mapping decisions:

- `Patient` maps from `patient_runtime`
- `ServiceRequest` maps from `lis_order_item_runtime`
- `Specimen` maps from `specimen_runtime`
- `Task` maps from `task_work_runtime`
- `Observation` maps from `observation_runtime`
- `DiagnosticReport` maps from `diagnostic_report_runtime`
- `AuditEvent` maps from `audit_event_log_runtime`
- `Provenance` maps from `provenance_record_runtime`

Current search support is intentionally practical rather than exhaustive. The facade now accepts:

- `Patient`: `identifier`, `family`, `_id`
- `ServiceRequest`: `patient`, `identifier`, `requisition`, `status`, `_id`
- `Specimen`: `patient`, `identifier`, `accession`, `status`, `_id`
- `Task`: `status`, `focus`, `code`, `patient`, `_id`
- `Observation`: `patient`, `specimen`, `status`, `code`, `based-on`, `_id`
- `DiagnosticReport`: `patient`, `based-on`, `status`, `_id`
- `AuditEvent`: `entity`, `_id`
- `Provenance`: `target`, `_id`

The current facade also enriches several resources beyond the first read-only baseline:

- `ServiceRequest.requisition`
- `Specimen.accessionIdentifier` and `Specimen.request`
- `Task.code` and `Task.for`
- `Observation.referenceRange` from the stored snapshot when available
- `DiagnosticReport.basedOn`, `DiagnosticReport.specimen`, and `DiagnosticReport.presentedForm`

Current limits:

- no FHIR write interactions,
- no subscriptions,
- no profile validation layer,
- search parameters are intentionally narrow and operational, not exhaustive.
