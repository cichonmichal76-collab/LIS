from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    DiagnosticReportRecord,
    DiagnosticReportVersionRecord,
    ObservationRecord,
    OrderItemRecord,
    OrderRecord,
    ReportObservationRecord,
)
from app.schemas.reports import (
    AmendReportRequest,
    AuthorizeReportRequest,
    CreateReportRequest,
    DiagnosticReportSummary,
    DiagnosticReportVersionSummary,
)
from app.services.audit import write_audit_event
from app.services.provenance import write_provenance_record


def generate_report(
    session: Session,
    payload: CreateReportRequest,
    *,
    actor_user_id: str | None = None,
) -> DiagnosticReportSummary:
    order = _get_order_or_404(session, payload.order_id)
    observations = session.scalars(
        select(ObservationRecord)
        .join(OrderItemRecord, ObservationRecord.order_item_id == OrderItemRecord.id)
        .where(OrderItemRecord.order_id == order.id)
        .where(ObservationRecord.status.not_in(["cancelled", "entered_in_error"]))
        .order_by(ObservationRecord.created_at.asc())
    ).all()
    if not observations:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot generate a report without observations on the order.",
        )

    report = DiagnosticReportRecord(
        id=str(uuid4()),
        report_no=_generate_identifier("REP"),
        order_id=order.id,
        patient_id=order.patient_id,
        status="preliminary",
        category_code="laboratory",
        code_local=payload.code_local,
        code_loinc=payload.code_loinc,
        effective_at=datetime.now(UTC),
        conclusion_text=payload.conclusion_text,
        current_version_no=1,
    )
    session.add(report)
    for index, observation in enumerate(observations, start=1):
        session.add(
            ReportObservationRecord(
                id=str(uuid4()),
                report=report,
                observation=observation,
                sort_order=index,
            )
        )

    version = _create_report_version(
        report=report,
        version_no=1,
        status="preliminary",
        payload={
            "report_no": report.report_no,
            "status": "preliminary",
            "order_id": order.id,
            "observation_ids": [observation.id for observation in observations],
            "conclusion_text": payload.conclusion_text,
        },
    )
    session.add(version)
    write_audit_event(
        session,
        entity_type="diagnostic_report",
        entity_id=report.id,
        action="generate",
        status=report.status,
        context={"actor_user_id": actor_user_id, "order_id": order.id},
    )
    write_provenance_record(
        session,
        target_resource_type="diagnostic_report",
        target_resource_id=report.id,
        activity_code="report-generated",
        based_on_order_id=order.id,
        report_version_id=version.id,
        agent_user_id=actor_user_id,
        inputs=payload.model_dump(mode="json"),
    )
    session.commit()
    return get_report(session, UUID(report.id))


def get_report(session: Session, report_id: UUID) -> DiagnosticReportSummary:
    report = _get_report_or_404(session, report_id)
    return _to_report_summary(report)


def render_report_pdf(session: Session, report_id: UUID, *, version_no: int | None = None) -> bytes:
    report = _get_report_or_404(session, report_id)
    effective_version_no = version_no or report.current_version_no
    version = next((item for item in report.versions if item.version_no == effective_version_no), None)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} does not have version {effective_version_no}.",
        )

    payload = version.payload or {}
    conclusion_text = payload.get("conclusion_text") or report.conclusion_text
    lines = [
        f"PDF placeholder for report {report.report_no}",
        f"report_id={report.id}",
        f"version={version.version_no}",
        f"status={version.status}",
        f"patient_id={report.patient_id}",
        f"order_id={report.order_id}",
    ]
    if conclusion_text:
        lines.append(f"conclusion={conclusion_text}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def authorize_report(
    session: Session,
    report_id: UUID,
    payload: AuthorizeReportRequest,
    *,
    actor_user_id: str | None = None,
) -> DiagnosticReportSummary:
    report = _get_report_or_404(session, report_id)
    if report.status not in {"registered", "partial", "preliminary"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Report {report_id} cannot be authorized from status '{report.status}'.",
        )

    signed_at = datetime.now(UTC)
    next_version_no = report.current_version_no + 1
    version = _create_report_version(
        report=report,
        version_no=next_version_no,
        status="final",
        payload={
            "report_no": report.report_no,
            "status": "final",
            "signed_by_user_id": str(payload.signed_by_user_id),
            "authorized_at": signed_at.isoformat(),
        },
        signed_by_user_id=str(payload.signed_by_user_id),
        signed_at=signed_at,
    )
    session.add(version)
    report.status = "final"
    report.issued_at = signed_at
    report.current_version_no = next_version_no
    write_audit_event(
        session,
        entity_type="diagnostic_report",
        entity_id=report.id,
        action="authorize",
        status=report.status,
        context={
            "actor_user_id": actor_user_id,
            "signed_by_user_id": str(payload.signed_by_user_id),
        },
    )
    write_provenance_record(
        session,
        target_resource_type="diagnostic_report",
        target_resource_id=report.id,
        activity_code="report-authorized",
        based_on_order_id=report.order_id,
        report_version_id=version.id,
        agent_user_id=str(payload.signed_by_user_id),
        inputs=payload.model_dump(mode="json"),
    )
    session.commit()
    return get_report(session, report_id)


def amend_report(
    session: Session,
    report_id: UUID,
    payload: AmendReportRequest,
    *,
    actor_user_id: str | None = None,
) -> DiagnosticReportSummary:
    report = _get_report_or_404(session, report_id)
    if report.status not in {"final", "amended", "corrected"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Report {report_id} must be final before amendment.",
        )

    next_version_no = report.current_version_no + 1
    conclusion_text = payload.conclusion_text if payload.conclusion_text is not None else report.conclusion_text
    version = _create_report_version(
        report=report,
        version_no=next_version_no,
        status="amended",
        payload={
            "report_no": report.report_no,
            "status": "amended",
            "reason": payload.reason,
            "conclusion_text": conclusion_text,
            "signed_by_user_id": str(payload.signed_by_user_id),
        },
        amendment_reason=payload.reason,
        signed_by_user_id=str(payload.signed_by_user_id),
        signed_at=datetime.now(UTC),
    )
    session.add(version)
    report.status = "amended"
    report.conclusion_text = conclusion_text
    report.current_version_no = next_version_no
    write_audit_event(
        session,
        entity_type="diagnostic_report",
        entity_id=report.id,
        action="amend",
        status=report.status,
        context={"actor_user_id": actor_user_id, **payload.model_dump(mode="json")},
    )
    write_provenance_record(
        session,
        target_resource_type="diagnostic_report",
        target_resource_id=report.id,
        activity_code="report-amended",
        based_on_order_id=report.order_id,
        report_version_id=version.id,
        agent_user_id=str(payload.signed_by_user_id),
        inputs=payload.model_dump(mode="json"),
    )
    session.commit()
    return get_report(session, report_id)


def _create_report_version(
    *,
    report: DiagnosticReportRecord,
    version_no: int,
    status: str,
    payload: dict[str, object],
    signed_by_user_id: str | None = None,
    signed_at: datetime | None = None,
    amendment_reason: str | None = None,
) -> DiagnosticReportVersionRecord:
    return DiagnosticReportVersionRecord(
        id=str(uuid4()),
        report=report,
        version_no=version_no,
        status=status,
        amendment_reason=amendment_reason,
        rendered_pdf_uri=f"/api/v1/reports/{report.id}/pdf?version={version_no}",
        signed_by_user_id=signed_by_user_id,
        signed_at=signed_at,
        payload=payload,
    )


def _get_order_or_404(session: Session, order_id: UUID) -> OrderRecord:
    order = session.get(OrderRecord, str(order_id))
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} was not found.",
        )
    return order


def _get_report_or_404(session: Session, report_id: UUID) -> DiagnosticReportRecord:
    stmt: Select[tuple[DiagnosticReportRecord]] = (
        select(DiagnosticReportRecord)
        .options(
            selectinload(DiagnosticReportRecord.versions),
            selectinload(DiagnosticReportRecord.report_observations),
        )
        .where(DiagnosticReportRecord.id == str(report_id))
    )
    report = session.scalar(stmt)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} was not found.",
        )
    return report


def _generate_identifier(prefix: str) -> str:
    return f"{prefix}-{datetime.now(UTC):%Y%m%d%H%M%S}-{uuid4().hex[:8].upper()}"


def _to_report_summary(report: DiagnosticReportRecord) -> DiagnosticReportSummary:
    return DiagnosticReportSummary(
        id=report.id,
        report_no=report.report_no,
        order_id=report.order_id,
        patient_id=report.patient_id,
        status=report.status,
        category_code=report.category_code,
        code_local=report.code_local,
        code_loinc=report.code_loinc,
        effective_at=report.effective_at,
        issued_at=report.issued_at,
        conclusion_text=report.conclusion_text,
        current_version_no=report.current_version_no,
        versions=[
            DiagnosticReportVersionSummary(
                id=version.id,
                report_id=version.report_id,
                version_no=version.version_no,
                status=version.status,
                amendment_reason=version.amendment_reason,
                rendered_pdf_uri=version.rendered_pdf_uri,
                signed_by_user_id=version.signed_by_user_id,
                signed_at=version.signed_at,
                payload=version.payload,
                created_at=version.created_at,
            )
            for version in report.versions
        ],
        observation_ids=[
            UUID(report_observation.observation_id) for report_observation in report.report_observations
        ],
    )
