from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import APP_VERSION
from app.db.models import (
    AuditEventRecord,
    DiagnosticReportRecord,
    ObservationRecord,
    OrderItemRecord,
    OrderRecord,
    PatientRecord,
    ProvenanceRecord,
    SpecimenRecord,
    TaskRecord,
    TestCatalogRecord,
)

FHIR_BASE = "/fhir/R4"

SERVICE_REQUEST_STATUS_MAP = {
    "draft": "draft",
    "registered": "active",
    "accepted": "active",
    "in_collection": "active",
    "received": "active",
    "in_process": "active",
    "tech_review": "active",
    "med_review": "active",
    "released": "completed",
    "amended": "completed",
    "cancelled": "revoked",
    "on_hold": "on-hold",
}

SPECIMEN_STATUS_MAP = {
    "expected": "unavailable",
    "collected": "available",
    "received": "available",
    "accepted": "available",
    "aliquoted": "available",
    "in_process": "available",
    "stored": "available",
    "rejected": "unsatisfactory",
    "disposed": "unavailable",
}

TASK_STATUS_MAP = {
    "created": "requested",
    "ready": "ready",
    "in_progress": "in-progress",
    "on_hold": "on-hold",
    "completed": "completed",
    "failed": "failed",
    "cancelled": "cancelled",
}

FHIR_STATUS_IDENTITY = {
    "registered": "registered",
    "preliminary": "preliminary",
    "final": "final",
    "amended": "amended",
    "corrected": "corrected",
    "cancelled": "cancelled",
    "entered_in_error": "entered-in-error",
    "partial": "partial",
}


def capability_statement() -> dict[str, Any]:
    resource_names = [
        "Patient",
        "ServiceRequest",
        "Specimen",
        "Task",
        "Observation",
        "DiagnosticReport",
        "AuditEvent",
        "Provenance",
    ]
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": datetime.now(UTC).isoformat(),
        "kind": "instance",
        "fhirVersion": "4.0.1",
        "format": ["json", "application/fhir+json"],
        "software": {"name": "lis-core", "version": APP_VERSION},
        "implementation": {"description": "LIS read/search FHIR facade"},
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": resource_name,
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                    }
                    for resource_name in resource_names
                ],
            }
        ],
    }


def read_patient_resource(session: Session, patient_id: UUID) -> dict[str, Any]:
    patient = session.get(PatientRecord, str(patient_id))
    if patient is None:
        raise _resource_not_found("Patient", patient_id)
    return _patient_to_fhir(patient)


def search_patient_resources(
    session: Session,
    *,
    identifier: str | None = None,
    family: str | None = None,
    resource_id: UUID | None = None,
) -> dict[str, Any]:
    stmt: Select[tuple[PatientRecord]] = select(PatientRecord).order_by(PatientRecord.created_at.desc())
    if resource_id:
        stmt = stmt.where(PatientRecord.id == str(resource_id))
    if identifier:
        stmt = stmt.where(PatientRecord.mrn == _parse_identifier_search(identifier))
    if family:
        stmt = stmt.where(PatientRecord.family_name.ilike(f"%{family}%"))
    resources = [_patient_to_fhir(patient) for patient in session.scalars(stmt).all()]
    return _bundle(resources)


def read_service_request_resource(session: Session, service_request_id: UUID) -> dict[str, Any]:
    item, order, catalog = _get_service_request_row_or_404(session, service_request_id)
    specimens = session.scalars(select(SpecimenRecord).where(SpecimenRecord.order_id == order.id)).all()
    return _service_request_to_fhir(item, order, catalog, specimens)


def search_service_request_resources(
    session: Session,
    *,
    patient: str | None = None,
    identifier: str | None = None,
    requisition: str | None = None,
    status_filter: str | None = None,
    resource_id: UUID | None = None,
) -> dict[str, Any]:
    stmt = (
        select(OrderItemRecord, OrderRecord, TestCatalogRecord)
        .join(OrderRecord, OrderItemRecord.order_id == OrderRecord.id)
        .outerjoin(TestCatalogRecord, OrderItemRecord.test_catalog_id == TestCatalogRecord.id)
        .order_by(OrderRecord.ordered_at.desc(), OrderItemRecord.line_no.asc())
    )
    patient_id = _parse_reference_id(patient)
    if resource_id:
        stmt = stmt.where(OrderItemRecord.id == str(resource_id))
    if patient_id:
        stmt = stmt.where(OrderRecord.patient_id == patient_id)
    requisition_value = _parse_identifier_search(requisition or identifier)
    if requisition_value:
        stmt = stmt.where(OrderRecord.requisition_no == requisition_value)

    rows = session.execute(stmt).all()
    specimens_by_order = _specimens_by_order(session, [order.id for _, order, _ in rows])
    resources = [
        _service_request_to_fhir(item, order, catalog, specimens_by_order.get(order.id, []))
        for item, order, catalog in rows
    ]
    if status_filter:
        resources = [resource for resource in resources if resource.get("status") == status_filter]
    return _bundle(resources)


def read_specimen_resource(session: Session, specimen_id: UUID) -> dict[str, Any]:
    specimen = session.get(SpecimenRecord, str(specimen_id))
    if specimen is None:
        raise _resource_not_found("Specimen", specimen_id)
    order_item_ids = _order_item_ids_by_order(session, [specimen.order_id]).get(specimen.order_id, [])
    return _specimen_to_fhir(specimen, order_item_ids)


def search_specimen_resources(
    session: Session,
    *,
    patient: str | None = None,
    identifier: str | None = None,
    accession: str | None = None,
    status_filter: str | None = None,
    resource_id: UUID | None = None,
) -> dict[str, Any]:
    stmt: Select[tuple[SpecimenRecord]] = select(SpecimenRecord).order_by(SpecimenRecord.created_at.desc())
    patient_id = _parse_reference_id(patient)
    if resource_id:
        stmt = stmt.where(SpecimenRecord.id == str(resource_id))
    if patient_id:
        stmt = stmt.where(SpecimenRecord.patient_id == patient_id)
    accession_value = _parse_identifier_search(accession or identifier)
    if accession_value:
        stmt = stmt.where(SpecimenRecord.accession_no == accession_value)
    specimens = session.scalars(stmt).all()
    order_item_ids_by_order = _order_item_ids_by_order(session, [specimen.order_id for specimen in specimens])
    resources = [
        _specimen_to_fhir(specimen, order_item_ids_by_order.get(specimen.order_id, []))
        for specimen in specimens
    ]
    if status_filter:
        resources = [resource for resource in resources if resource.get("status") == status_filter]
    return _bundle(resources)


def read_task_resource(session: Session, task_id: UUID) -> dict[str, Any]:
    task, patient_id = _get_task_row_or_404(session, task_id)
    return _task_to_fhir(task, patient_id=patient_id)


def search_task_resources(
    session: Session,
    *,
    status_filter: str | None = None,
    focus: str | None = None,
    code: str | None = None,
    patient: str | None = None,
    resource_id: UUID | None = None,
) -> dict[str, Any]:
    stmt = (
        select(TaskRecord, OrderRecord.patient_id)
        .outerjoin(OrderItemRecord, TaskRecord.based_on_order_item_id == OrderItemRecord.id)
        .outerjoin(OrderRecord, OrderItemRecord.order_id == OrderRecord.id)
        .order_by(TaskRecord.authored_on.desc())
    )
    if resource_id:
        stmt = stmt.where(TaskRecord.id == str(resource_id))
    focus_id = _parse_reference_id(focus)
    if focus_id:
        stmt = stmt.where(TaskRecord.focus_id == focus_id)
    if code:
        stmt = stmt.where(TaskRecord.queue_code == code)
    patient_id = _parse_reference_id(patient)
    if patient_id:
        stmt = stmt.where(OrderRecord.patient_id == patient_id)

    resources = [
        _task_to_fhir(task, patient_id=row_patient_id)
        for task, row_patient_id in session.execute(stmt).all()
    ]
    if status_filter:
        resources = [resource for resource in resources if resource.get("status") == status_filter]
    return _bundle(resources)


def read_observation_resource(session: Session, observation_id: UUID) -> dict[str, Any]:
    observation, order_item, order, _patient = _get_observation_row_or_404(session, observation_id)
    return _observation_to_fhir(observation, order_item, order)


def search_observation_resources(
    session: Session,
    *,
    patient: str | None = None,
    specimen: str | None = None,
    status_filter: str | None = None,
    code: str | None = None,
    based_on: str | None = None,
    resource_id: UUID | None = None,
) -> dict[str, Any]:
    stmt = (
        select(ObservationRecord, OrderItemRecord, OrderRecord, PatientRecord)
        .join(OrderItemRecord, ObservationRecord.order_item_id == OrderItemRecord.id)
        .join(OrderRecord, OrderItemRecord.order_id == OrderRecord.id)
        .join(PatientRecord, OrderRecord.patient_id == PatientRecord.id)
        .order_by(ObservationRecord.created_at.desc())
    )
    if resource_id:
        stmt = stmt.where(ObservationRecord.id == str(resource_id))
    patient_id = _parse_reference_id(patient)
    if patient_id:
        stmt = stmt.where(OrderRecord.patient_id == patient_id)
    specimen_id = _parse_reference_id(specimen)
    if specimen_id:
        stmt = stmt.where(ObservationRecord.specimen_id == specimen_id)
    if code:
        stmt = stmt.where(
            (ObservationRecord.code_local == code) | (ObservationRecord.code_loinc == code)
        )
    based_on_id = _parse_reference_id(based_on)
    if based_on_id:
        stmt = stmt.where(ObservationRecord.order_item_id == based_on_id)
    resources = [
        _observation_to_fhir(observation, order_item, order)
        for observation, order_item, order, _patient in session.execute(stmt).all()
    ]
    if status_filter:
        resources = [resource for resource in resources if resource.get("status") == status_filter]
    return _bundle(resources)


def read_diagnostic_report_resource(session: Session, report_id: UUID) -> dict[str, Any]:
    report = _get_report_or_404(session, report_id)
    based_on_ids = _order_item_ids_by_order(session, [report.order_id]).get(report.order_id, [])
    specimen_ids = [specimen.id for specimen in _specimens_by_order(session, [report.order_id]).get(report.order_id, [])]
    return _diagnostic_report_to_fhir(report, based_on_ids=based_on_ids, specimen_ids=specimen_ids)


def search_diagnostic_report_resources(
    session: Session,
    *,
    patient: str | None = None,
    based_on: str | None = None,
    status_filter: str | None = None,
    resource_id: UUID | None = None,
) -> dict[str, Any]:
    stmt: Select[tuple[DiagnosticReportRecord]] = (
        select(DiagnosticReportRecord)
        .options(
            selectinload(DiagnosticReportRecord.report_observations),
            selectinload(DiagnosticReportRecord.versions),
        )
        .order_by(DiagnosticReportRecord.created_at.desc())
    )
    if resource_id:
        stmt = stmt.where(DiagnosticReportRecord.id == str(resource_id))
    patient_id = _parse_reference_id(patient)
    if patient_id:
        stmt = stmt.where(DiagnosticReportRecord.patient_id == patient_id)
    based_on_id = _parse_reference_id(based_on)
    if based_on_id:
        order_id_stmt = select(OrderItemRecord.order_id).where(OrderItemRecord.id == based_on_id)
        stmt = stmt.where(DiagnosticReportRecord.order_id == order_id_stmt.scalar_subquery())

    reports = session.scalars(stmt).all()
    based_on_by_order = _order_item_ids_by_order(session, [report.order_id for report in reports])
    specimens_by_order = _specimens_by_order(session, [report.order_id for report in reports])
    resources = [
        _diagnostic_report_to_fhir(
            report,
            based_on_ids=based_on_by_order.get(report.order_id, []),
            specimen_ids=[specimen.id for specimen in specimens_by_order.get(report.order_id, [])],
        )
        for report in reports
    ]
    if status_filter:
        resources = [resource for resource in resources if resource.get("status") == status_filter]
    return _bundle(resources)


def read_audit_event_resource(session: Session, audit_event_id: UUID) -> dict[str, Any]:
    audit_event = session.get(AuditEventRecord, str(audit_event_id))
    if audit_event is None:
        raise _resource_not_found("AuditEvent", audit_event_id)
    return _audit_event_to_fhir(audit_event)


def search_audit_event_resources(
    session: Session,
    *,
    entity: str | None = None,
    resource_id: UUID | None = None,
) -> dict[str, Any]:
    stmt: Select[tuple[AuditEventRecord]] = select(AuditEventRecord).order_by(AuditEventRecord.event_at.desc())
    if resource_id:
        stmt = stmt.where(AuditEventRecord.id == str(resource_id))
    resources = [_audit_event_to_fhir(audit_event) for audit_event in session.scalars(stmt).all()]
    if entity:
        resources = [resource for resource in resources if _audit_matches_entity(resource, entity)]
    return _bundle(resources)


def read_provenance_resource(session: Session, provenance_id: UUID) -> dict[str, Any]:
    provenance = session.get(ProvenanceRecord, str(provenance_id))
    if provenance is None:
        raise _resource_not_found("Provenance", provenance_id)
    return _provenance_to_fhir(provenance)


def search_provenance_resources(
    session: Session,
    *,
    target: str | None = None,
    resource_id: UUID | None = None,
) -> dict[str, Any]:
    stmt: Select[tuple[ProvenanceRecord]] = select(ProvenanceRecord).order_by(
        ProvenanceRecord.recorded_at.desc()
    )
    if resource_id:
        stmt = stmt.where(ProvenanceRecord.id == str(resource_id))
    resources = [_provenance_to_fhir(provenance) for provenance in session.scalars(stmt).all()]
    if target:
        target_reference = _normalize_reference(target)
        resources = [
            resource
            for resource in resources
            if any(entry.get("reference") == target_reference for entry in resource.get("target", []))
        ]
    return _bundle(resources)


def _bundle(resources: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(resources),
        "entry": [
            {
                "fullUrl": f"{FHIR_BASE}/{resource['resourceType']}/{resource['id']}",
                "resource": resource,
                "search": {"mode": "match"},
            }
            for resource in resources
        ],
    }


def _patient_to_fhir(patient: PatientRecord) -> dict[str, Any]:
    resource: dict[str, Any] = {
        "resourceType": "Patient",
        "id": patient.id,
        "identifier": [{"system": "urn:lis:mrn", "value": patient.mrn}],
        "active": True,
        "name": [{"family": patient.family_name, "given": [patient.given_name]}],
    }
    if patient.birth_date:
        resource["birthDate"] = patient.birth_date.isoformat()
    if patient.sex_code:
        resource["gender"] = _map_gender(patient.sex_code)
    return resource


def _service_request_to_fhir(
    item: OrderItemRecord,
    order: OrderRecord,
    catalog: TestCatalogRecord | None,
    specimens: list[SpecimenRecord],
) -> dict[str, Any]:
    resource: dict[str, Any] = {
        "resourceType": "ServiceRequest",
        "id": item.id,
        "identifier": [
            {"system": "urn:lis:requisition", "value": order.requisition_no},
            {"system": "urn:lis:order-item", "value": item.id},
        ],
        "requisition": {"system": "urn:lis:requisition", "value": order.requisition_no},
        "status": SERVICE_REQUEST_STATUS_MAP.get(item.status, "active"),
        "intent": "order",
        "subject": _reference("Patient", order.patient_id),
        "priority": item.priority or order.priority,
        "authoredOn": order.ordered_at.isoformat(),
    }
    if catalog:
        resource["code"] = _codeable_concept(
            local_code=catalog.local_code,
            local_display=catalog.display_name,
            loinc_code=catalog.loinc_num,
        )
    elif item.test_catalog_id:
        resource["code"] = {"text": item.test_catalog_id}
    if item.requested_specimen_type_code:
        resource["specimenCode"] = [{"text": item.requested_specimen_type_code}]
    if specimens:
        resource["specimen"] = [_reference("Specimen", specimen.id) for specimen in specimens]
    if order.clinical_info:
        resource["note"] = [{"text": order.clinical_info}]
    return resource


def _specimen_to_fhir(specimen: SpecimenRecord, request_ids: list[str]) -> dict[str, Any]:
    resource: dict[str, Any] = {
        "resourceType": "Specimen",
        "id": specimen.id,
        "identifier": [{"system": "urn:lis:accession", "value": specimen.accession_no}],
        "accessionIdentifier": {"system": "urn:lis:accession", "value": specimen.accession_no},
        "status": SPECIMEN_STATUS_MAP.get(specimen.status, "available"),
        "type": {"text": specimen.specimen_type_code},
        "subject": _reference("Patient", specimen.patient_id),
    }
    if specimen.collected_at:
        resource["collection"] = {"collectedDateTime": specimen.collected_at.isoformat()}
    if specimen.received_at:
        resource["receivedTime"] = specimen.received_at.isoformat()
    if request_ids:
        resource["request"] = [_reference("ServiceRequest", request_id) for request_id in request_ids]
    if specimen.notes:
        resource["note"] = [{"text": specimen.notes}]
    return resource


def _task_to_fhir(task: TaskRecord, *, patient_id: str | None = None) -> dict[str, Any]:
    resource: dict[str, Any] = {
        "resourceType": "Task",
        "id": task.id,
        "identifier": [{"system": "urn:lis:task", "value": task.id}],
        "status": TASK_STATUS_MAP.get(task.status, task.status),
        "intent": "order",
        "authoredOn": task.authored_on.isoformat(),
        "focus": _reference(_map_focus_type(task.focus_type), task.focus_id),
        "code": _codeable_concept(
            local_code=task.queue_code,
            local_display=task.business_status or task.queue_code,
            loinc_code=None,
        ),
    }
    if patient_id:
        resource["for"] = _reference("Patient", patient_id)
    if task.based_on_order_item_id:
        resource["basedOn"] = [_reference("ServiceRequest", task.based_on_order_item_id)]
    if task.business_status:
        resource["businessStatus"] = {"text": task.business_status}
    if task.owner_user_id:
        resource["owner"] = {"display": task.owner_user_id}
    if task.started_at or task.completed_at:
        resource["executionPeriod"] = {}
        if task.started_at:
            resource["executionPeriod"]["start"] = task.started_at.isoformat()
        if task.completed_at:
            resource["executionPeriod"]["end"] = task.completed_at.isoformat()
    return resource


def _observation_to_fhir(
    observation: ObservationRecord,
    order_item: OrderItemRecord,
    order: OrderRecord,
) -> dict[str, Any]:
    resource: dict[str, Any] = {
        "resourceType": "Observation",
        "id": observation.id,
        "status": FHIR_STATUS_IDENTITY.get(observation.status, observation.status),
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                    }
                ],
                "text": "Laboratory",
            }
        ],
        "code": _codeable_concept(
            local_code=observation.code_local,
            local_display=observation.code_local,
            loinc_code=observation.code_loinc,
        ),
        "subject": _reference("Patient", order.patient_id),
        "basedOn": [_reference("ServiceRequest", order_item.id)],
    }
    if observation.specimen_id:
        resource["specimen"] = _reference("Specimen", observation.specimen_id)
    if observation.effective_at:
        resource["effectiveDateTime"] = observation.effective_at.isoformat()
    if observation.issued_at:
        resource["issued"] = observation.issued_at.isoformat()
    if observation.interpretation_code or observation.abnormal_flag:
        resource["interpretation"] = [
            {"text": observation.interpretation_code or observation.abnormal_flag}
        ]
    if observation.method_code:
        resource["method"] = {"text": observation.method_code}
    resource.update(_value_component(observation))

    reference_range = _reference_range_component(observation)
    if reference_range:
        resource["referenceRange"] = [reference_range]
    return resource


def _diagnostic_report_to_fhir(
    report: DiagnosticReportRecord,
    *,
    based_on_ids: list[str],
    specimen_ids: list[str],
) -> dict[str, Any]:
    result_refs = [
        _reference("Observation", report_observation.observation_id)
        for report_observation in report.report_observations
    ]
    latest_version = report.versions[-1] if report.versions else None
    resource: dict[str, Any] = {
        "resourceType": "DiagnosticReport",
        "id": report.id,
        "identifier": [{"system": "urn:lis:report", "value": report.report_no}],
        "status": FHIR_STATUS_IDENTITY.get(report.status, report.status),
        "code": _codeable_concept(
            local_code=report.code_local,
            local_display=report.code_local or "Laboratory report",
            loinc_code=report.code_loinc,
        ),
        "subject": _reference("Patient", report.patient_id),
        "result": result_refs,
    }
    if based_on_ids:
        resource["basedOn"] = [_reference("ServiceRequest", order_item_id) for order_item_id in based_on_ids]
    if specimen_ids:
        resource["specimen"] = [_reference("Specimen", specimen_id) for specimen_id in specimen_ids]
    if report.effective_at:
        resource["effectiveDateTime"] = report.effective_at.isoformat()
    if report.issued_at:
        resource["issued"] = report.issued_at.isoformat()
    if report.conclusion_text:
        resource["conclusion"] = report.conclusion_text
    rendered_pdf_uri = (
        latest_version.rendered_pdf_uri
        if latest_version and latest_version.rendered_pdf_uri
        else f"/api/v1/reports/{report.id}/pdf?version={report.current_version_no}"
    )
    resource["presentedForm"] = [
        {
            "contentType": "application/pdf",
            "url": rendered_pdf_uri,
            "title": f"Report {report.report_no}",
        }
    ]
    return resource


def _audit_event_to_fhir(audit_event: AuditEventRecord) -> dict[str, Any]:
    context = audit_event.context or {}
    actor_username = context.get("actor_username")
    resource: dict[str, Any] = {
        "resourceType": "AuditEvent",
        "id": audit_event.id,
        "type": {
            "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
            "code": "rest",
            "display": "RESTful Operation",
        },
        "action": _audit_action_code(audit_event.action),
        "recorded": audit_event.event_at.isoformat(),
        "outcome": "0",
        "agent": [{"who": {"display": actor_username or "system"}}],
        "entity": [
            {
                "what": {
                    "reference": _entity_reference(audit_event.entity_type, audit_event.entity_id),
                }
            }
        ],
    }
    return resource


def _provenance_to_fhir(provenance: ProvenanceRecord) -> dict[str, Any]:
    resource: dict[str, Any] = {
        "resourceType": "Provenance",
        "id": provenance.id,
        "target": [
            _reference(
                _map_entity_type(provenance.target_resource_type),
                provenance.target_resource_id,
            )
        ],
        "recorded": provenance.recorded_at.isoformat(),
        "activity": {"text": provenance.activity_code},
    }
    if provenance.agent_user_id:
        resource["agent"] = [{"who": {"display": provenance.agent_user_id}}]
    entity_reference = _provenance_entity_reference(provenance)
    if entity_reference:
        resource["entity"] = [{"role": "source", "what": entity_reference}]
    return resource


def _value_component(observation: ObservationRecord) -> dict[str, Any]:
    if observation.value_type == "quantity":
        value_quantity: dict[str, Any] = {"value": observation.value_num}
        if observation.unit_ucum:
            value_quantity["unit"] = observation.unit_ucum
            value_quantity["system"] = "http://unitsofmeasure.org"
            value_quantity["code"] = observation.unit_ucum
        return {"valueQuantity": value_quantity}
    if observation.value_type == "boolean":
        return {"valueBoolean": observation.value_boolean}
    if observation.value_type == "coded":
        return {
            "valueCodeableConcept": {
                "coding": [
                    {
                        "system": observation.value_code_system,
                        "code": observation.value_code,
                    }
                ]
            }
        }
    return {"valueString": observation.value_text}


def _reference_range_component(observation: ObservationRecord) -> dict[str, Any] | None:
    snapshot = observation.reference_interval_snapshot or {}
    if not snapshot:
        return None

    reference_range: dict[str, Any] = {}
    low = snapshot.get("low")
    high = snapshot.get("high")
    if low is not None:
        reference_range["low"] = _quantity(low, observation.unit_ucum)
    if high is not None:
        reference_range["high"] = _quantity(high, observation.unit_ucum)
    if snapshot.get("text"):
        reference_range["text"] = snapshot["text"]
    return reference_range or None


def _quantity(value: Any, unit_ucum: str | None) -> dict[str, Any]:
    quantity = {"value": value}
    if unit_ucum:
        quantity["unit"] = unit_ucum
        quantity["system"] = "http://unitsofmeasure.org"
        quantity["code"] = unit_ucum
    return quantity


def _codeable_concept(
    *,
    local_code: str | None,
    local_display: str | None,
    loinc_code: str | None,
) -> dict[str, Any]:
    codings: list[dict[str, Any]] = []
    if local_code:
        codings.append(
            {
                "system": "urn:lis:local-code",
                "code": local_code,
                "display": local_display or local_code,
            }
        )
    if loinc_code:
        codings.append(
            {
                "system": "http://loinc.org",
                "code": loinc_code,
            }
        )
    concept: dict[str, Any] = {"coding": codings}
    if local_display:
        concept["text"] = local_display
    return concept


def _reference(resource_type: str, resource_id: str, display: str | None = None) -> dict[str, Any]:
    reference: dict[str, Any] = {"reference": f"{resource_type}/{resource_id}"}
    if display:
        reference["display"] = display
    return reference


def _map_gender(sex_code: str) -> str:
    normalized = sex_code.strip().lower()
    if normalized in {"m", "male"}:
        return "male"
    if normalized in {"f", "female"}:
        return "female"
    return "unknown"


def _map_focus_type(focus_type: str) -> str:
    return {
        "order-item": "ServiceRequest",
        "specimen": "Specimen",
        "observation": "Observation",
        "report": "DiagnosticReport",
    }.get(focus_type, "Basic")


def _map_entity_type(entity_type: str) -> str:
    return {
        "patient": "Patient",
        "order": "ServiceRequest",
        "order-item": "ServiceRequest",
        "specimen": "Specimen",
        "task": "Task",
        "observation": "Observation",
        "diagnostic_report": "DiagnosticReport",
        "report": "DiagnosticReport",
        "user": "Practitioner",
        "test-catalog": "Basic",
    }.get(entity_type, "Basic")


def _entity_reference(entity_type: str, entity_id: str) -> str:
    return f"{_map_entity_type(entity_type)}/{entity_id}"


def _audit_action_code(action: str) -> str:
    normalized = action.lower()
    if normalized in {"create", "bootstrap-admin", "append-item", "replacement-create"}:
        return "C"
    if normalized in {"read", "search"}:
        return "R"
    if normalized in {"delete"}:
        return "D"
    return "U"


def _audit_matches_entity(resource: dict[str, Any], entity: str) -> bool:
    normalized_entity = _normalize_reference(entity)
    references = [
        entry.get("what", {}).get("reference")
        for entry in resource.get("entity", [])
        if entry.get("what", {}).get("reference")
    ]
    if normalized_entity in references:
        return True
    entity_id = _parse_reference_id(entity)
    return any(reference.endswith(f"/{entity_id}") for reference in references)


def _provenance_entity_reference(provenance: ProvenanceRecord) -> dict[str, Any] | None:
    if provenance.based_on_order_item_id:
        return _reference("ServiceRequest", provenance.based_on_order_item_id)
    if provenance.based_on_order_id:
        return _reference("ServiceRequest", provenance.based_on_order_id)
    if provenance.specimen_id:
        return _reference("Specimen", provenance.specimen_id)
    if provenance.observation_id:
        return _reference("Observation", provenance.observation_id)
    return None


def _parse_reference_id(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip()
    if "|" in value:
        value = value.split("|", 1)[1]
    if "/" in value:
        value = value.split("/", 1)[1]
    return value or None


def _normalize_reference(raw: str) -> str:
    if "/" in raw:
        return raw
    return raw


def _parse_identifier_search(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip()
    if "|" in value:
        value = value.split("|", 1)[1]
    return value or None


def _get_service_request_row_or_404(
    session: Session,
    service_request_id: UUID,
) -> tuple[OrderItemRecord, OrderRecord, TestCatalogRecord | None]:
    row = session.execute(
        select(OrderItemRecord, OrderRecord, TestCatalogRecord)
        .join(OrderRecord, OrderItemRecord.order_id == OrderRecord.id)
        .outerjoin(TestCatalogRecord, OrderItemRecord.test_catalog_id == TestCatalogRecord.id)
        .where(OrderItemRecord.id == str(service_request_id))
    ).first()
    if row is None:
        raise _resource_not_found("ServiceRequest", service_request_id)
    return row


def _get_task_row_or_404(session: Session, task_id: UUID) -> tuple[TaskRecord, str | None]:
    row = session.execute(
        select(TaskRecord, OrderRecord.patient_id)
        .outerjoin(OrderItemRecord, TaskRecord.based_on_order_item_id == OrderItemRecord.id)
        .outerjoin(OrderRecord, OrderItemRecord.order_id == OrderRecord.id)
        .where(TaskRecord.id == str(task_id))
    ).first()
    if row is None:
        raise _resource_not_found("Task", task_id)
    return row


def _get_observation_row_or_404(
    session: Session,
    observation_id: UUID,
) -> tuple[ObservationRecord, OrderItemRecord, OrderRecord, PatientRecord]:
    row = session.execute(
        select(ObservationRecord, OrderItemRecord, OrderRecord, PatientRecord)
        .join(OrderItemRecord, ObservationRecord.order_item_id == OrderItemRecord.id)
        .join(OrderRecord, OrderItemRecord.order_id == OrderRecord.id)
        .join(PatientRecord, OrderRecord.patient_id == PatientRecord.id)
        .where(ObservationRecord.id == str(observation_id))
    ).first()
    if row is None:
        raise _resource_not_found("Observation", observation_id)
    return row


def _get_report_or_404(session: Session, report_id: UUID) -> DiagnosticReportRecord:
    report = session.scalar(
        select(DiagnosticReportRecord)
        .options(
            selectinload(DiagnosticReportRecord.report_observations),
            selectinload(DiagnosticReportRecord.versions),
        )
        .where(DiagnosticReportRecord.id == str(report_id))
    )
    if report is None:
        raise _resource_not_found("DiagnosticReport", report_id)
    return report


def _order_item_ids_by_order(session: Session, order_ids: list[str]) -> dict[str, list[str]]:
    if not order_ids:
        return {}
    rows = session.execute(
        select(OrderItemRecord.order_id, OrderItemRecord.id)
        .where(OrderItemRecord.order_id.in_(order_ids))
        .order_by(OrderItemRecord.line_no.asc())
    ).all()
    grouped: dict[str, list[str]] = {}
    for order_id, order_item_id in rows:
        grouped.setdefault(order_id, []).append(order_item_id)
    return grouped


def _specimens_by_order(
    session: Session,
    order_ids: list[str],
) -> dict[str, list[SpecimenRecord]]:
    if not order_ids:
        return {}
    specimens = session.scalars(select(SpecimenRecord).where(SpecimenRecord.order_id.in_(order_ids))).all()
    grouped: dict[str, list[SpecimenRecord]] = {}
    for specimen in specimens:
        grouped.setdefault(specimen.order_id, []).append(specimen)
    return grouped


def _resource_not_found(resource_type: str, resource_id: UUID) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource_type} {resource_id} was not found.",
    )
