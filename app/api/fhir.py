from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.services import fhir as fhir_service

router = APIRouter(prefix="/fhir/R4", tags=["fhir"])


@router.get("/metadata")
def get_metadata() -> dict:
    return fhir_service.capability_statement()


@router.get("/Patient")
def search_patients(
    session: DbSession,
    identifier: str | None = Query(default=None),
    family: str | None = Query(default=None),
    resource_id: UUID | None = Query(default=None, alias="_id"),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.search_patient_resources(
        session,
        identifier=identifier,
        family=family,
        resource_id=resource_id,
    )


@router.get("/Patient/{patient_id}")
def read_patient(
    patient_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.read_patient_resource(session, patient_id)


@router.get("/ServiceRequest")
def search_service_requests(
    session: DbSession,
    patient: str | None = Query(default=None),
    identifier: str | None = Query(default=None),
    requisition: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    resource_id: UUID | None = Query(default=None, alias="_id"),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.search_service_request_resources(
        session,
        patient=patient,
        identifier=identifier,
        requisition=requisition,
        status_filter=status_filter,
        resource_id=resource_id,
    )


@router.get("/ServiceRequest/{service_request_id}")
def read_service_request(
    service_request_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.read_service_request_resource(session, service_request_id)


@router.get("/Specimen")
def search_specimens(
    session: DbSession,
    patient: str | None = Query(default=None),
    identifier: str | None = Query(default=None),
    accession: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    resource_id: UUID | None = Query(default=None, alias="_id"),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.search_specimen_resources(
        session,
        patient=patient,
        identifier=identifier,
        accession=accession,
        status_filter=status_filter,
        resource_id=resource_id,
    )


@router.get("/Specimen/{specimen_id}")
def read_specimen(
    specimen_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.read_specimen_resource(session, specimen_id)


@router.get("/Task")
def search_tasks(
    session: DbSession,
    status_filter: str | None = Query(default=None, alias="status"),
    focus: str | None = Query(default=None),
    code: str | None = Query(default=None),
    patient: str | None = Query(default=None),
    resource_id: UUID | None = Query(default=None, alias="_id"),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.search_task_resources(
        session,
        status_filter=status_filter,
        focus=focus,
        code=code,
        patient=patient,
        resource_id=resource_id,
    )


@router.get("/Task/{task_id}")
def read_task(
    task_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.read_task_resource(session, task_id)


@router.get("/Observation")
def search_observations(
    session: DbSession,
    patient: str | None = Query(default=None),
    specimen: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    code: str | None = Query(default=None),
    based_on: str | None = Query(default=None, alias="based-on"),
    resource_id: UUID | None = Query(default=None, alias="_id"),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.search_observation_resources(
        session,
        patient=patient,
        specimen=specimen,
        status_filter=status_filter,
        code=code,
        based_on=based_on,
        resource_id=resource_id,
    )


@router.get("/Observation/{observation_id}")
def read_observation(
    observation_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.read_observation_resource(session, observation_id)


@router.get("/DiagnosticReport")
def search_diagnostic_reports(
    session: DbSession,
    patient: str | None = Query(default=None),
    based_on: str | None = Query(default=None, alias="based-on"),
    status_filter: str | None = Query(default=None, alias="status"),
    resource_id: UUID | None = Query(default=None, alias="_id"),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.search_diagnostic_report_resources(
        session,
        patient=patient,
        based_on=based_on,
        status_filter=status_filter,
        resource_id=resource_id,
    )


@router.get("/DiagnosticReport/{report_id}")
def read_diagnostic_report(
    report_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.read_diagnostic_report_resource(session, report_id)


@router.get("/AuditEvent")
def search_audit_events(
    session: DbSession,
    entity: str | None = Query(default=None),
    resource_id: UUID | None = Query(default=None, alias="_id"),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.search_audit_event_resources(
        session,
        entity=entity,
        resource_id=resource_id,
    )


@router.get("/AuditEvent/{audit_event_id}")
def read_audit_event(
    audit_event_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.read_audit_event_resource(session, audit_event_id)


@router.get("/Provenance")
def search_provenance(
    session: DbSession,
    target: str | None = Query(default=None),
    resource_id: UUID | None = Query(default=None, alias="_id"),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.search_provenance_resources(
        session,
        target=target,
        resource_id=resource_id,
    )


@router.get("/Provenance/{provenance_id}")
def read_provenance(
    provenance_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict:
    return fhir_service.read_provenance_resource(session, provenance_id)
