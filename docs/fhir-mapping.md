# FHIR Mapping

## Core Resource Mapping

- `patient` -> `Patient`
- `organization` -> `Organization`
- `location` -> `Location`
- `practitioner` -> `Practitioner`
- `practitioner_role` -> `PractitionerRole`
- `device` -> `Device`
- `lis_order_item` -> `ServiceRequest`
- `lis_order.requisition_no` -> `ServiceRequest.requisition`
- `specimen` -> `Specimen`
- `task_work` -> `Task`
- `observation` -> `Observation`
- `diagnostic_report` -> `DiagnosticReport`
- `audit_event_log` -> `AuditEvent`
- `provenance_record` -> `Provenance`

## Notes

### `lis_order` and `lis_order_item`

- `lis_order` stays an internal grouping object.
- `lis_order_item` maps to the externally visible `ServiceRequest`.
- Requisition and `groupIdentifier` preserve grouping semantics.

### `specimen` and `container`

- Base FHIR `Specimen` covers only the basic specimen representation.
- Hierarchical containers stay in the local relational model.
- Optional FHIR extensions can expose selected container details to integrations.

### `task_work`

- `Task.basedOn` maps back to `ServiceRequest`.
- `Task.groupIdentifier` can represent requisition grouping or batch grouping.
- `Task.businessStatus` is the right place for richer local workflow semantics.

### `observation_link`

- `has_member` -> `Observation.hasMember`
- `derived_from` -> `Observation.derivedFrom`
- `triggered_by` -> `Observation.triggeredBy`
- `replaces` and `sequel_to` can stay local or move into explicit extensions

### `diagnostic_report`

- `DiagnosticReport.basedOn` points back to relevant `ServiceRequest` resources.
- `DiagnosticReport.result` points to atomic observations.
- The final PDF can be exposed through `presentedForm`.

### audit and provenance

- `AuditEvent` answers who did what and when and where.
- `Provenance` answers what inputs and agents produced or signed the data.
