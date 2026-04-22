from __future__ import annotations

import json
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import (
    ContainerRecord,
    DeviceRecord,
    DeviceTestMapRecord,
    DiagnosticReportRecord,
    InterfaceMessageLogRecord,
    ObservationRecord,
    OrderItemRecord,
    OrderRecord,
    PatientRecord,
    RawInstrumentMessageRecord,
    ReportObservationRecord,
    SpecimenEventRecord,
    SpecimenRecord,
    TaskRecord,
    TestCatalogRecord,
)
from app.schemas.autoverification import AutoverificationApplyResponse
from app.schemas.integrations import (
    ASTMImportResponse,
    ASTMMessageImportRequest,
    DeviceGatewayIngestRequest,
    DeviceGatewayIngestResponse,
    DeviceWorklistItem,
    DeviceWorklistResponse,
    HL7MessageImportRequest,
    HL7OrderImportResponse,
    HL7ResultImportResponse,
    IntegratedObservationSummary,
    InterfaceMessageSummary,
    MessageDirection,
    RawInstrumentMessageSummary,
)
from app.schemas.observations import ObservationSummary
from app.schemas.orders import OrderItemSummary, OrderSummary
from app.schemas.patients import PatientSummary
from app.schemas.specimens import SpecimenSummary
from app.services.audit import write_audit_event
from app.services import autoverification as autoverification_service
from app.services.astm import astm_ts_to_datetime, build_astm_worklist, parse_astm_message
from app.services.hl7v2 import (
    HL7Message,
    build_segment,
    code_parts,
    date_to_hl7_date,
    datetime_to_hl7_ts,
    first_non_empty,
    hl7_date_to_date,
    hl7_ts_to_datetime,
    join_segments,
    map_internal_observation_status_to_obx,
    map_obx_status_to_internal,
    map_report_status_to_obr,
    parse_hl7_message,
)
from app.services.provenance import write_provenance_record

READABLE_SPECIMEN_STATUSES = {"accepted", "in_process", "received", "collected"}
VERIFIED_OBSERVATION_STATUSES = {"final", "corrected"}


def list_interface_messages(
    session: Session,
    *,
    protocol: str | None = None,
    direction: MessageDirection | None = None,
    message_type: str | None = None,
) -> list[InterfaceMessageSummary]:
    stmt: Select[tuple[InterfaceMessageLogRecord]] = select(InterfaceMessageLogRecord).order_by(
        InterfaceMessageLogRecord.created_at.desc()
    )
    if protocol:
        stmt = stmt.where(InterfaceMessageLogRecord.protocol == protocol)
    if direction:
        stmt = stmt.where(InterfaceMessageLogRecord.direction == direction.value)
    if message_type:
        stmt = stmt.where(InterfaceMessageLogRecord.message_type == message_type)
    return [_to_interface_message_summary(row) for row in session.scalars(stmt).all()]


def list_device_messages(
    session: Session,
    *,
    device_id: UUID | None = None,
) -> list[RawInstrumentMessageSummary]:
    stmt: Select[tuple[RawInstrumentMessageRecord]] = select(RawInstrumentMessageRecord).order_by(
        RawInstrumentMessageRecord.created_at.desc()
    )
    if device_id:
        stmt = stmt.where(RawInstrumentMessageRecord.device_id == str(device_id))
    return [_to_raw_message_summary(row) for row in session.scalars(stmt).all()]


def import_hl7_oml_o33(
    session: Session,
    payload: HL7MessageImportRequest,
    *,
    actor_user_id: str | None = None,
) -> HL7OrderImportResponse:
    try:
        message = parse_hl7_message(payload.message)
        message_type = message.message_type() or "OML^O33"
        if not (message_type.startswith("OML^O33") or message_type.startswith("ORM^O01")):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported HL7 order message type: {message_type}",
            )

        control_id = message.control_id() or _generate_identifier("HL7")
        _ensure_message_not_processed(session, message_type=message_type, control_id=control_id)

        pid = _require_segment(message, "PID", "PID segment is required")
        mrn = pid.first_component(3)
        if not mrn:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="PID-3 MRN is required.",
            )

        patient_name = pid.components(5)
        patient = _get_or_create_patient(
            session,
            mrn=mrn,
            given_name=patient_name[1] if len(patient_name) > 1 else "Unknown",
            family_name=patient_name[0] if patient_name else "Unknown",
            sex_code=_sex_from_hl7(pid.field(8)),
            birth_date=hl7_date_to_date(pid.field(7)),
            create_if_missing=payload.create_missing_patient,
        )

        msh = _require_segment(message, "MSH", "MSH segment is required")
        source_system = first_non_empty(msh.field(3), msh.field(4), "hl7v2") or "hl7v2"
        orc = message.segment("ORC")
        first_obr = _require_segment(message, "OBR", "At least one OBR segment is required")
        requisition_no = first_non_empty(
            orc.field(2) if orc else None,
            orc.field(3) if orc else None,
            first_obr.field(2),
            first_obr.field(3),
            control_id,
        ) or _generate_identifier("REQ")
        priority = _hl7_priority_to_internal(first_obr.field(27) or (orc.field(7) if orc else None))
        clinical_info = first_non_empty(first_obr.field(13), first_obr.field(31))
        order = _get_or_create_order(
            session,
            requisition_no=requisition_no,
            patient_id=patient.id,
            source_system=source_system,
            priority=priority,
            clinical_info=clinical_info,
        )

        current_specimen_type: str | None = None
        created_specimens: list[SpecimenRecord] = []
        for segment in message.segments:
            if segment.name == "SPM":
                current_specimen_type = (
                    first_non_empty(segment.first_component(4), current_specimen_type, "UNK") or "UNK"
                )
                accession_no = first_non_empty(segment.first_component(2), segment.first_component(3))
                specimen = _create_expected_specimen(
                    session,
                    order=order,
                    patient=patient,
                    specimen_type_code=current_specimen_type,
                    accession_no=accession_no,
                    notes="Imported from HL7 OML^O33",
                )
                if specimen not in created_specimens:
                    created_specimens.append(specimen)
            elif segment.name == "OBR":
                service_code, _, coding_system = code_parts(segment.field(4))
                catalog = _resolve_catalog_by_code(session, service_code, coding_system)
                if catalog is None:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"No test catalog mapping for OBR-4 code {service_code}.",
                    )
                _ensure_order_item(
                    session,
                    order=order,
                    catalog=catalog,
                    requested_specimen_type_code=current_specimen_type or catalog.specimen_type_code,
                    priority=priority,
                )

        if not created_specimens:
            first_item = session.scalar(
                select(OrderItemRecord)
                .where(OrderItemRecord.order_id == order.id)
                .order_by(OrderItemRecord.line_no.asc())
            )
            if first_item is not None:
                catalog = _get_catalog_or_404(session, UUID(first_item.test_catalog_id))
                created_specimens.append(
                    _create_expected_specimen(
                        session,
                        order=order,
                        patient=patient,
                        specimen_type_code=first_item.requested_specimen_type_code
                        or catalog.specimen_type_code
                        or "UNK",
                        accession_no=None,
                        notes="Auto-created from HL7 order import",
                    )
                )

        message_log = _create_interface_message_log(
            session,
            protocol="hl7v2",
            direction="inbound",
            message_type=message_type,
            control_id=control_id,
            payload=payload.message,
            related_entity_type="order",
            related_entity_id=order.id,
            processed_ok=True,
        )
        write_audit_event(
            session,
            entity_type="interface_message_log",
            entity_id=message_log.id,
            action="hl7-import-oml-o33",
            status="processed",
            context={"actor_user_id": actor_user_id, "order_id": order.id},
        )
        session.commit()

        items = session.scalars(
            select(OrderItemRecord)
            .where(OrderItemRecord.order_id == order.id)
            .order_by(OrderItemRecord.line_no.asc())
        ).all()
        specimens = session.scalars(
            select(SpecimenRecord)
            .where(SpecimenRecord.order_id == order.id)
            .order_by(SpecimenRecord.created_at.asc())
        ).all()
        return HL7OrderImportResponse(
            message_log_id=message_log.id,
            patient=_to_patient_summary(patient),
            order=_to_order_summary(order),
            items=[_to_order_item_summary(item) for item in items],
            specimens=[_to_specimen_summary(specimen) for specimen in specimens],
        )
    except HTTPException as exc:
        session.rollback()
        _log_hl7_failure(session, payload.message, default_message_type="OML^O33", detail=str(exc.detail))
        raise
    except Exception as exc:
        session.rollback()
        _log_hl7_failure(session, payload.message, default_message_type="OML^O33", detail=str(exc))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process HL7 OML^O33: {exc}",
        ) from exc


def import_hl7_oru_r01(
    session: Session,
    payload: HL7MessageImportRequest,
    *,
    actor_user_id: str | None = None,
) -> HL7ResultImportResponse:
    try:
        message = parse_hl7_message(payload.message)
        message_type = message.message_type() or "ORU^R01"
        if not message_type.startswith("ORU^R01"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported HL7 result message type: {message_type}",
            )

        control_id = message.control_id() or _generate_identifier("HL7")
        _ensure_message_not_processed(session, message_type=message_type, control_id=control_id)

        spm = message.segment("SPM")
        accession_no = first_non_empty(
            spm.first_component(2) if spm else None,
            spm.first_component(3) if spm else None,
        )
        orc = message.segment("ORC")
        first_obr = _require_segment(message, "OBR", "At least one OBR segment is required")
        requisition_no = first_non_empty(
            orc.field(2) if orc else None,
            orc.field(3) if orc else None,
            first_obr.field(2),
            first_obr.field(3),
        )

        specimen = _find_specimen_by_accession_or_barcode(session, accession_no, None)
        order: OrderRecord | None = None
        if specimen is not None:
            order = session.get(OrderRecord, specimen.order_id)
        elif requisition_no:
            order = session.scalar(select(OrderRecord).where(OrderRecord.requisition_no == requisition_no))
            if order is not None:
                specimen = session.scalar(
                    select(SpecimenRecord)
                    .where(SpecimenRecord.order_id == order.id)
                    .order_by(SpecimenRecord.created_at.asc())
                )
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not resolve order from ORU message.",
            )

        current_obr_catalog: TestCatalogRecord | None = None
        current_order_item: OrderItemRecord | None = None
        created_observations: list[ObservationRecord] = []
        for segment in message.segments:
            if segment.name == "OBR":
                code, _, coding_system = code_parts(segment.field(4))
                current_obr_catalog = _resolve_catalog_by_code(session, code, coding_system)
                current_order_item = None
                if current_obr_catalog is not None:
                    current_order_item = _resolve_order_item_for_catalog(
                        session,
                        order_id=order.id,
                        test_catalog_id=current_obr_catalog.id,
                    )
            elif segment.name == "OBX":
                obx_code, _, obx_coding_system = code_parts(segment.field(3))
                catalog = _resolve_catalog_by_code(session, obx_code, obx_coding_system) or current_obr_catalog
                if catalog is None:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"No test catalog mapping for OBX-3 code {obx_code}.",
                    )
                order_item = current_order_item or _resolve_order_item_for_catalog(
                    session,
                    order_id=order.id,
                    test_catalog_id=catalog.id,
                )
                if order_item is None:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Order item not found for mapped catalog code {catalog.local_code}.",
                    )

                (
                    internal_value_type,
                    value_num,
                    value_text,
                    value_boolean,
                    value_code_system,
                    value_code,
                ) = _parse_obx_value(segment.field(2), segment.field(5))
                status_value = map_obx_status_to_internal(segment.field(11))
                observation = ObservationRecord(
                    id=str(uuid4()),
                    order_item_id=order_item.id,
                    specimen_id=specimen.id if specimen else None,
                    code_local=catalog.local_code,
                    code_loinc=catalog.loinc_num,
                    status=status_value,
                    category_code="laboratory",
                    value_type=internal_value_type,
                    value_num=value_num,
                    value_text=value_text,
                    value_boolean=value_boolean,
                    value_code_system=value_code_system,
                    value_code=value_code,
                    unit_ucum=(segment.field(6).split("^")[0] if segment.field(6) else None)
                    or catalog.default_ucum,
                    abnormal_flag=segment.field(8) or None,
                    effective_at=hl7_ts_to_datetime(
                        first_non_empty(segment.field(14), segment.field(19), first_obr.field(7))
                    ),
                    issued_at=datetime.now(UTC)
                    if status_value in {"preliminary", "final", "corrected"}
                    else None,
                    reference_interval_snapshot={"hl7_reference_range": segment.field(7)}
                    if segment.field(7)
                    else {},
                )
                session.add(observation)
                created_observations.append(observation)
                order_item.status = "tech_review" if status_value in {"preliminary", "final", "corrected"} else "in_process"
                if specimen is not None and specimen.status in {"expected", "collected", "received", "accepted"}:
                    specimen.status = "in_process"
                write_provenance_record(
                    session,
                    target_resource_type="observation",
                    target_resource_id=observation.id,
                    activity_code="hl7v2-oru-import",
                    based_on_order_id=order.id,
                    based_on_order_item_id=order_item.id,
                    specimen_id=specimen.id if specimen else None,
                    observation_id=observation.id,
                    agent_user_id=actor_user_id,
                    inputs={"control_id": control_id},
                )

        if not created_observations:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No OBX observations were created from the message.",
            )

        message_log = _create_interface_message_log(
            session,
            protocol="hl7v2",
            direction="inbound",
            message_type=message_type,
            control_id=control_id,
            payload=payload.message,
            related_entity_type="order",
            related_entity_id=order.id,
            processed_ok=True,
        )
        write_audit_event(
            session,
            entity_type="interface_message_log",
            entity_id=message_log.id,
            action="hl7-import-oru-r01",
            status="processed",
            context={"actor_user_id": actor_user_id, "order_id": order.id},
        )
        session.commit()
        return HL7ResultImportResponse(
            message_log_id=message_log.id,
            order_id=order.id,
            specimen_id=specimen.id if specimen else None,
            created_observation_ids=[observation.id for observation in created_observations],
            observations=[_to_observation_summary(observation) for observation in created_observations],
        )
    except HTTPException as exc:
        session.rollback()
        _log_hl7_failure(session, payload.message, default_message_type="ORU^R01", detail=str(exc.detail))
        raise
    except Exception as exc:
        session.rollback()
        _log_hl7_failure(session, payload.message, default_message_type="ORU^R01", detail=str(exc))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process HL7 ORU^R01: {exc}",
        ) from exc


def export_hl7_oml_o33(
    session: Session,
    order_id: UUID,
    *,
    actor_user_id: str | None = None,
) -> str:
    order = _get_order_or_404(session, order_id)
    patient = _get_patient_or_404(session, UUID(order.patient_id))
    items = session.scalars(
        select(OrderItemRecord)
        .where(OrderItemRecord.order_id == order.id)
        .order_by(OrderItemRecord.line_no.asc())
    ).all()
    if not items:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order has no items to export.",
        )

    catalog_lookup = _catalog_lookup_for_order_items(session, items)
    specimens = session.scalars(
        select(SpecimenRecord)
        .where(SpecimenRecord.order_id == order.id)
        .order_by(SpecimenRecord.created_at.asc())
    ).all()
    control_id = _generate_identifier("HL7")
    segments = [
        build_segment(
            "MSH",
            [
                "^~\\&",
                "LIS-CORE",
                "LIS",
                "DOWNSTREAM",
                "LAB",
                datetime_to_hl7_ts(datetime.now(UTC)),
                "",
                "OML^O33",
                control_id,
                "P",
                "2.5.1",
            ],
        ),
        build_segment(
            "PID",
            [
                "1",
                "",
                f"{patient.mrn}^^^LIS^MR",
                "",
                f"{patient.family_name}^{patient.given_name}",
                "",
                date_to_hl7_date(patient.birth_date),
                patient.sex_code or "",
            ],
        ),
        build_segment(
            "ORC",
            ["NW", order.requisition_no, order.requisition_no, "", "", "", order.priority],
        ),
    ]
    for specimen in specimens:
        segments.append(
            build_segment(
                "SPM",
                [
                    "1",
                    f"{specimen.accession_no}^LIS",
                    "",
                    f"{specimen.specimen_type_code}^{specimen.specimen_type_code}^L",
                ],
            )
        )
    for index, item in enumerate(items, start=1):
        catalog = catalog_lookup[item.test_catalog_id]
        code_field = (
            f"{catalog.loinc_num}^{catalog.display_name}^LN"
            if catalog.loinc_num
            else f"{catalog.local_code}^{catalog.display_name}^L"
        )
        segments.append(
            build_segment(
                "OBR",
                [
                    str(index),
                    order.requisition_no,
                    order.requisition_no,
                    code_field,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    order.clinical_info or "",
                ],
            )
        )
    hl7_message = join_segments(segments)
    message_log = _create_interface_message_log(
        session,
        protocol="hl7v2",
        direction="outbound",
        message_type="OML^O33",
        control_id=control_id,
        payload=hl7_message,
        related_entity_type="order",
        related_entity_id=order.id,
        processed_ok=True,
    )
    write_audit_event(
        session,
        entity_type="interface_message_log",
        entity_id=message_log.id,
        action="hl7-export-oml-o33",
        status="processed",
        context={"actor_user_id": actor_user_id, "order_id": order.id},
    )
    session.commit()
    return hl7_message


def export_hl7_oru_r01(
    session: Session,
    report_id: UUID,
    *,
    actor_user_id: str | None = None,
) -> str:
    report = _get_report_or_404(session, report_id)
    order = _get_order_or_404(session, UUID(report.order_id))
    patient = _get_patient_or_404(session, UUID(report.patient_id))
    report_observations = session.scalars(
        select(ReportObservationRecord)
        .where(ReportObservationRecord.report_id == report.id)
        .order_by(ReportObservationRecord.sort_order.asc())
    ).all()
    if not report_observations:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report has no observations to export.",
        )

    observation_ids = [row.observation_id for row in report_observations]
    observations = session.scalars(
        select(ObservationRecord)
        .where(ObservationRecord.id.in_(observation_ids))
        .order_by(ObservationRecord.created_at.asc())
    ).all()
    observation_lookup = {observation.id: observation for observation in observations}
    items = session.scalars(
        select(OrderItemRecord)
        .where(OrderItemRecord.order_id == order.id)
        .order_by(OrderItemRecord.line_no.asc())
    ).all()
    item_lookup = {item.id: item for item in items}
    catalog_lookup = _catalog_lookup_for_order_items(session, items)
    specimens = session.scalars(
        select(SpecimenRecord)
        .where(SpecimenRecord.order_id == order.id)
        .order_by(SpecimenRecord.created_at.asc())
    ).all()
    specimen = specimens[0] if specimens else None
    control_id = _generate_identifier("HL7")

    grouped: dict[str, list[ObservationRecord]] = {}
    for report_observation in report_observations:
        observation = observation_lookup.get(report_observation.observation_id)
        if observation is None:
            continue
        grouped.setdefault(observation.order_item_id, []).append(observation)

    segments = [
        build_segment(
            "MSH",
            [
                "^~\\&",
                "LIS-CORE",
                "LIS",
                "EHR",
                "HOSPITAL",
                datetime_to_hl7_ts(datetime.now(UTC)),
                "",
                "ORU^R01",
                control_id,
                "P",
                "2.5.1",
            ],
        ),
        build_segment(
            "PID",
            [
                "1",
                "",
                f"{patient.mrn}^^^LIS^MR",
                "",
                f"{patient.family_name}^{patient.given_name}",
                "",
                date_to_hl7_date(patient.birth_date),
                patient.sex_code or "",
            ],
        ),
    ]
    if specimen is not None:
        segments.append(
            build_segment(
                "SPM",
                [
                    "1",
                    f"{specimen.accession_no}^LIS",
                    "",
                    f"{specimen.specimen_type_code}^{specimen.specimen_type_code}^L",
                ],
            )
        )

    obr_index = 0
    for order_item_id, obs_list in grouped.items():
        item = item_lookup.get(order_item_id)
        if item is None:
            continue
        catalog = catalog_lookup[item.test_catalog_id]
        obr_index += 1
        code_field = (
            f"{catalog.loinc_num}^{catalog.display_name}^LN"
            if catalog.loinc_num
            else f"{catalog.local_code}^{catalog.display_name}^L"
        )
        segments.append(build_segment("ORC", ["RE", order.requisition_no, report.report_no]))
        segments.append(
            build_segment(
                "OBR",
                [
                    str(obr_index),
                    order.requisition_no,
                    report.report_no,
                    code_field,
                    "",
                    "",
                    datetime_to_hl7_ts(report.effective_at),
                    "",
                    "",
                    "",
                    "",
                    "",
                    order.clinical_info or "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    map_report_status_to_obr(report.status),
                ],
            )
        )
        for obx_index, observation in enumerate(obs_list, start=1):
            obs_code = (
                f"{observation.code_loinc}^{catalog.display_name}^LN"
                if observation.code_loinc
                else f"{observation.code_local}^{catalog.display_name}^L"
            )
            value_type, value, units = _format_obx_value(observation)
            segments.append(
                build_segment(
                    "OBX",
                    [
                        str(obx_index),
                        value_type,
                        obs_code,
                        "",
                        value,
                        units,
                        "",
                        observation.abnormal_flag or "",
                        "",
                        "",
                        map_internal_observation_status_to_obx(observation.status),
                        "",
                        "",
                        datetime_to_hl7_ts(observation.effective_at),
                    ],
                )
            )

    hl7_message = join_segments(segments)
    message_log = _create_interface_message_log(
        session,
        protocol="hl7v2",
        direction="outbound",
        message_type="ORU^R01",
        control_id=control_id,
        payload=hl7_message,
        related_entity_type="diagnostic_report",
        related_entity_id=report.id,
        processed_ok=True,
    )
    write_audit_event(
        session,
        entity_type="interface_message_log",
        entity_id=message_log.id,
        action="hl7-export-oru-r01",
        status="processed",
        context={"actor_user_id": actor_user_id, "report_id": report.id},
    )
    session.commit()
    return hl7_message


def export_astm_worklist(
    session: Session,
    device_id: UUID,
    *,
    actor_user_id: str | None = None,
) -> str:
    device = _get_device_or_404(session, device_id)
    worklist = get_device_worklist(session, device_id)
    message = build_astm_worklist(
        device.code or "DEVICE",
        [item.model_dump(mode="json") for item in worklist.items],
    )
    control_id = _generate_identifier("ASTM")
    message_log = _create_interface_message_log(
        session,
        protocol="astm",
        direction="outbound",
        message_type="ASTM-WORKLIST",
        control_id=control_id,
        payload=message,
        related_entity_type="device",
        related_entity_id=device.id,
        processed_ok=True,
    )
    write_audit_event(
        session,
        entity_type="device",
        entity_id=device.id,
        action="export-astm-worklist",
        status="processed",
        context={
            "actor_user_id": actor_user_id,
            "control_id": control_id,
            "item_count": len(worklist.items),
            "message_log_id": message_log.id,
        },
    )
    session.commit()
    return message


def import_astm_results(
    session: Session,
    payload: ASTMMessageImportRequest,
    *,
    actor_user_id: str | None = None,
) -> ASTMImportResponse:
    device = _get_device_or_404(session, payload.device_id)
    if not device.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device {payload.device_id} is inactive.",
        )
    try:
        message = parse_astm_message(payload.message)
    except ValueError as exc:
        _create_interface_message_log(
            session,
            protocol="astm",
            direction="inbound",
            message_type="ASTM-RESULTS",
            payload=payload.message,
            processed_ok=False,
            error_text=str(exc),
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    control_id = _generate_identifier("ASTM")
    raw_message = _create_raw_instrument_message(
        session,
        device=device,
        protocol="astm",
        direction="inbound",
        message_type="ASTM-RESULTS",
        accession_no=message.orders[0].accession_no if message.orders else None,
        specimen_barcode=None,
        payload=payload.message,
        parsed_ok=True,
        created_observation_count=0,
        parser_version="astm-driver-v1",
    )

    created_observations: list[tuple[ObservationRecord, AutoverificationApplyResponse | None]] = []
    errors: list[str] = []
    for order_block in message.orders:
        specimen = _find_specimen_by_accession_or_barcode(
            session,
            accession_no=order_block.accession_no,
            specimen_barcode=None,
        )
        if specimen is None:
            errors.append(f"Specimen not found for accession {order_block.accession_no}")
            continue
        order = _get_order_or_404(session, UUID(specimen.order_id))
        for result in order_block.results:
            code, _, coding_system = code_parts(result.get("test_id"))
            mapping = None
            if code:
                mapping = session.scalar(
                    select(DeviceTestMapRecord).where(
                        DeviceTestMapRecord.device_id == device.id,
                        DeviceTestMapRecord.incoming_test_code == code,
                        DeviceTestMapRecord.active.is_(True),
                    )
                )
            catalog = session.get(TestCatalogRecord, mapping.test_catalog_id) if mapping else None
            if catalog is None:
                catalog = _resolve_catalog_by_code(session, code, coding_system) if code else None
            if catalog is None:
                errors.append(f"No device mapping or catalog for ASTM test {result.get('test_id')}")
                continue
            order_item = _resolve_order_item_for_catalog(
                session,
                order_id=order.id,
                test_catalog_id=catalog.id,
            )
            if order_item is None:
                errors.append(f"Order item not found for ASTM code {catalog.local_code}")
                continue

            raw_value = (result.get("value") or "").strip()
            value_type = "text"
            value_num = None
            value_text = None
            try:
                value_num = float(raw_value)
                value_type = "quantity"
            except ValueError:
                value_text = raw_value
            observation = ObservationRecord(
                id=str(uuid4()),
                order_item_id=order_item.id,
                specimen_id=specimen.id,
                raw_message_id=raw_message.id,
                device_id=device.id,
                code_local=catalog.local_code,
                code_loinc=catalog.loinc_num,
                status="preliminary" if payload.auto_verify else _astm_status_to_internal(result.get("result_status")),
                category_code="laboratory",
                value_type=value_type,
                value_num=value_num,
                value_text=value_text,
                unit_ucum=(result.get("unit") or (mapping.default_unit_ucum if mapping else None) or catalog.default_ucum),
                abnormal_flag=result.get("abnormal_flag"),
                method_code=device.code,
                effective_at=astm_ts_to_datetime(result.get("observed_at")) or datetime.now(UTC),
                issued_at=None,
                reference_interval_snapshot={},
            )
            session.add(observation)
            order_item.status = "tech_review"
            if specimen.status in {"expected", "collected", "received", "accepted"}:
                specimen.status = "in_process"
            write_provenance_record(
                session,
                target_resource_type="observation",
                target_resource_id=observation.id,
                activity_code="astm-import",
                based_on_order_id=order.id,
                based_on_order_item_id=order_item.id,
                specimen_id=specimen.id,
                observation_id=observation.id,
                device_id=device.id,
                agent_user_id=actor_user_id,
                inputs={"test_id": result.get("test_id"), "raw_message_id": raw_message.id},
            )
            autoverification_result = None
            if payload.auto_verify:
                autoverification_result = autoverification_service.apply_autoverification(
                    session,
                    UUID(observation.id),
                    actor=None,
                    source_activity="astm-autoverification",
                )
            created_observations.append((observation, autoverification_result))

    raw_message.created_observation_count = len(created_observations)
    raw_message.parsed_ok = len(created_observations) > 0 and not errors
    raw_message.parse_error = "; ".join(errors) if errors else None
    _create_interface_message_log(
        session,
        protocol="astm",
        direction="inbound",
        message_type="ASTM-RESULTS",
        control_id=control_id,
        payload=payload.message,
        related_entity_type="device",
        related_entity_id=device.id,
        processed_ok=raw_message.parsed_ok,
        error_text=raw_message.parse_error,
    )
    write_audit_event(
        session,
        entity_type="raw_instrument_message",
        entity_id=raw_message.id,
        action="astm-import",
        status="processed" if raw_message.parsed_ok else "partial",
        context={
            "actor_user_id": actor_user_id,
            "device_id": device.id,
            "control_id": control_id,
            "created_count": len(created_observations),
            "errors": errors,
        },
    )
    session.commit()
    return ASTMImportResponse(
        raw_message_id=raw_message.id,
        device_id=device.id,
        created_observations=[
            _to_integrated_observation_summary(observation, autoverification)
            for observation, autoverification in created_observations
        ],
        errors=errors,
    )


def get_device_worklist(session: Session, device_id: UUID) -> DeviceWorklistResponse:
    device = _get_device_or_404(session, device_id)
    if not device.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device {device_id} is inactive.",
        )

    mappings = session.scalars(
        select(DeviceTestMapRecord).where(
            DeviceTestMapRecord.device_id == device.id,
            DeviceTestMapRecord.active.is_(True),
        )
    ).all()
    catalog_ids = {mapping.test_catalog_id for mapping in mappings}
    if not catalog_ids:
        return DeviceWorklistResponse(device_id=device.id, items=[])

    mapping_by_catalog = {mapping.test_catalog_id: mapping for mapping in mappings}
    catalog_lookup = {
        catalog.id: catalog
        for catalog in session.scalars(
            select(TestCatalogRecord).where(TestCatalogRecord.id.in_(catalog_ids))
        ).all()
    }
    items = session.scalars(
        select(OrderItemRecord)
        .where(OrderItemRecord.test_catalog_id.in_(catalog_ids))
        .order_by(OrderItemRecord.created_at.asc(), OrderItemRecord.line_no.asc())
    ).all()

    worklist: list[DeviceWorklistItem] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        specimen = session.scalar(
            select(SpecimenRecord)
            .where(
                SpecimenRecord.order_id == item.order_id,
                SpecimenRecord.status.in_(READABLE_SPECIMEN_STATUSES),
            )
            .order_by(SpecimenRecord.created_at.asc())
        )
        if specimen is None:
            continue
        existing_final = session.scalar(
            select(ObservationRecord.id).where(
                ObservationRecord.order_item_id == item.id,
                ObservationRecord.status.in_(VERIFIED_OBSERVATION_STATUSES),
            )
        )
        if existing_final is not None:
            continue
        mapping = mapping_by_catalog.get(item.test_catalog_id)
        catalog = catalog_lookup.get(item.test_catalog_id)
        order = session.get(OrderRecord, item.order_id)
        if mapping is None or catalog is None or order is None:
            continue
        dedupe_key = (item.id, mapping.incoming_test_code)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        worklist.append(
            DeviceWorklistItem(
                order_item_id=item.id,
                order_id=order.id,
                requisition_no=order.requisition_no,
                specimen_id=specimen.id,
                accession_no=specimen.accession_no,
                specimen_barcode=_first_specimen_barcode(session, specimen.id),
                incoming_test_code=mapping.incoming_test_code,
                test_catalog_id=catalog.id,
                local_code=catalog.local_code,
                display_name=catalog.display_name,
                loinc_num=catalog.loinc_num,
                order_item_status=item.status,
                specimen_status=specimen.status,
            )
        )
    return DeviceWorklistResponse(device_id=device.id, items=worklist)


def ingest_device_results(
    session: Session,
    payload: DeviceGatewayIngestRequest,
    *,
    actor_user_id: str | None = None,
) -> DeviceGatewayIngestResponse:
    device = _get_device_or_404(session, payload.device_id)
    if not device.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device {payload.device_id} is inactive.",
        )
    if not payload.accession_no and not payload.specimen_barcode:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either accession_no or specimen_barcode is required.",
        )

    specimen = _find_specimen_by_accession_or_barcode(
        session,
        accession_no=payload.accession_no,
        specimen_barcode=payload.specimen_barcode,
    )
    if specimen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specimen not found for accession/barcode.",
        )

    order = _get_order_or_404(session, UUID(specimen.order_id))
    raw_message = _create_raw_instrument_message(
        session,
        device=device,
        protocol=payload.protocol,
        direction="inbound",
        message_type="analyzer-results",
        accession_no=payload.accession_no,
        specimen_barcode=payload.specimen_barcode,
        payload=json.dumps(payload.model_dump(mode="json")),
        parsed_ok=True,
        created_observation_count=0,
    )

    created_observations: list[tuple[ObservationRecord, AutoverificationApplyResponse | None]] = []
    errors: list[str] = []
    for result in payload.results:
        mapping = session.scalar(
            select(DeviceTestMapRecord).where(
                DeviceTestMapRecord.device_id == device.id,
                DeviceTestMapRecord.incoming_test_code == result.incoming_test_code,
                DeviceTestMapRecord.active.is_(True),
            )
        )
        catalog = None
        if mapping is not None:
            catalog = session.get(TestCatalogRecord, mapping.test_catalog_id)
        if catalog is None:
            catalog = _resolve_catalog_by_code(session, result.incoming_test_code, None)
        if catalog is None:
            errors.append(f"No device mapping or catalog for incoming_test_code {result.incoming_test_code}")
            continue
        order_item = _resolve_order_item_for_catalog(
            session,
            order_id=order.id,
            test_catalog_id=catalog.id,
        )
        if order_item is None:
            errors.append(f"Order item not found for mapped code {catalog.local_code}")
            continue

        observation = ObservationRecord(
            id=str(uuid4()),
            order_item_id=order_item.id,
            specimen_id=specimen.id,
            device_id=device.id,
            raw_message_id=raw_message.id,
            code_local=catalog.local_code,
            code_loinc=catalog.loinc_num,
            status="preliminary",
            category_code="laboratory",
            value_type=result.value_type.value,
            value_num=result.value_num,
            value_text=result.value_text,
            value_boolean=result.value_boolean,
            value_code_system=result.value_code_system,
            value_code=result.value_code,
            unit_ucum=result.unit_ucum
            or (mapping.default_unit_ucum if mapping is not None else None)
            or catalog.default_ucum,
            abnormal_flag=result.abnormal_flag,
            method_code=device.code,
            effective_at=result.effective_at or datetime.now(UTC),
            issued_at=None,
            reference_interval_snapshot={},
        )
        session.add(observation)
        order_item.status = "tech_review"
        if specimen.status in {"expected", "collected", "received", "accepted"}:
            specimen.status = "in_process"
        _complete_related_task_if_any(session, order_item_id=order_item.id, device_id=device.id)
        write_provenance_record(
            session,
            target_resource_type="observation",
            target_resource_id=observation.id,
            activity_code="device-gateway-import",
            based_on_order_id=order.id,
            based_on_order_item_id=order_item.id,
            specimen_id=specimen.id,
            observation_id=observation.id,
            device_id=device.id,
            agent_user_id=actor_user_id,
            inputs={
                "incoming_test_code": result.incoming_test_code,
                "raw_message_id": raw_message.id,
            },
        )
        autoverification_result = None
        if payload.auto_verify:
            autoverification_result = autoverification_service.apply_autoverification(
                session,
                UUID(observation.id),
                actor=None,
                source_activity="device-gateway-autoverification",
            )
        created_observations.append((observation, autoverification_result))

    raw_message.created_observation_count = len(created_observations)
    raw_message.parsed_ok = len(created_observations) > 0 and not errors
    raw_message.parse_error = "; ".join(errors) if errors else None
    write_audit_event(
        session,
        entity_type="raw_instrument_message",
        entity_id=raw_message.id,
        action="device-ingest",
        status="processed" if raw_message.parsed_ok else "partial",
        context={
            "actor_user_id": actor_user_id,
            "device_id": device.id,
            "created_count": len(created_observations),
            "errors": errors,
        },
    )
    session.commit()
    return DeviceGatewayIngestResponse(
        raw_message_id=raw_message.id,
        device_id=device.id,
        order_id=order.id,
        specimen_id=specimen.id,
        created_observations=[
            _to_integrated_observation_summary(observation, autoverification)
            for observation, autoverification in created_observations
        ],
        errors=errors,
    )


def _get_or_create_patient(
    session: Session,
    *,
    mrn: str,
    given_name: str,
    family_name: str,
    sex_code: str | None,
    birth_date: date | None,
    create_if_missing: bool,
) -> PatientRecord:
    patient = session.scalar(select(PatientRecord).where(PatientRecord.mrn == mrn))
    if patient is not None:
        return patient
    if not create_if_missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient not found for MRN {mrn}.",
        )
    patient = PatientRecord(
        id=str(uuid4()),
        mrn=mrn,
        given_name=given_name or "Unknown",
        family_name=family_name or "Unknown",
        sex_code=sex_code,
        birth_date=birth_date,
    )
    session.add(patient)
    return patient


def _get_or_create_order(
    session: Session,
    *,
    requisition_no: str,
    patient_id: str,
    source_system: str,
    priority: str,
    clinical_info: str | None,
) -> OrderRecord:
    order = session.scalar(select(OrderRecord).where(OrderRecord.requisition_no == requisition_no))
    if order is not None:
        return order
    order = OrderRecord(
        id=str(uuid4()),
        requisition_no=requisition_no,
        patient_id=patient_id,
        source_system=source_system,
        priority=priority,
        status="registered",
        clinical_info=clinical_info,
        ordered_at=datetime.now(UTC),
    )
    session.add(order)
    return order


def _ensure_order_item(
    session: Session,
    *,
    order: OrderRecord,
    catalog: TestCatalogRecord,
    requested_specimen_type_code: str | None,
    priority: str,
) -> OrderItemRecord:
    existing = _resolve_order_item_for_catalog(
        session,
        order_id=order.id,
        test_catalog_id=catalog.id,
    )
    if existing is not None:
        return existing
    line_no = (
        session.scalar(
            select(OrderItemRecord.line_no)
            .where(OrderItemRecord.order_id == order.id)
            .order_by(OrderItemRecord.line_no.desc())
            .limit(1)
        )
        or 0
    ) + 1
    item = OrderItemRecord(
        id=str(uuid4()),
        order_id=order.id,
        line_no=line_no,
        test_catalog_id=catalog.id,
        requested_specimen_type_code=requested_specimen_type_code,
        status="registered",
        priority=priority,
        aoe_payload={},
    )
    session.add(item)
    return item


def _create_expected_specimen(
    session: Session,
    *,
    order: OrderRecord,
    patient: PatientRecord,
    specimen_type_code: str,
    accession_no: str | None,
    notes: str | None,
) -> SpecimenRecord:
    normalized_accession = accession_no or _generate_identifier("ACC")
    existing = session.scalar(
        select(SpecimenRecord).where(SpecimenRecord.accession_no == normalized_accession)
    )
    if existing is not None:
        return existing
    specimen = SpecimenRecord(
        id=str(uuid4()),
        accession_no=normalized_accession,
        order_id=order.id,
        patient_id=patient.id,
        specimen_type_code=specimen_type_code,
        status="expected",
        notes=notes,
    )
    session.add(specimen)
    session.add(
        SpecimenEventRecord(
            id=str(uuid4()),
            specimen=specimen,
            event_type="hl7-import-accession",
            details={"accession_no": normalized_accession},
        )
    )
    return specimen


def _resolve_catalog_by_code(
    session: Session,
    code: str | None,
    coding_system: str | None,
) -> TestCatalogRecord | None:
    if not code:
        return None
    normalized_system = (coding_system or "").strip().upper()
    if normalized_system in {"LN", "LOINC"}:
        catalog = session.scalar(
            select(TestCatalogRecord).where(
                TestCatalogRecord.loinc_num == code,
                TestCatalogRecord.active.is_(True),
            )
        )
        if catalog is not None:
            return catalog
    catalog = session.scalar(
        select(TestCatalogRecord).where(
            TestCatalogRecord.local_code == code,
            TestCatalogRecord.active.is_(True),
        )
    )
    if catalog is not None:
        return catalog
    return session.scalar(
        select(TestCatalogRecord).where(
            TestCatalogRecord.loinc_num == code,
            TestCatalogRecord.active.is_(True),
        )
    )


def _resolve_order_item_for_catalog(
    session: Session,
    *,
    order_id: str,
    test_catalog_id: str,
) -> OrderItemRecord | None:
    return session.scalar(
        select(OrderItemRecord)
        .where(
            OrderItemRecord.order_id == order_id,
            OrderItemRecord.test_catalog_id == test_catalog_id,
        )
        .order_by(OrderItemRecord.line_no.asc())
    )


def _find_specimen_by_accession_or_barcode(
    session: Session,
    accession_no: str | None,
    specimen_barcode: str | None,
) -> SpecimenRecord | None:
    if accession_no:
        specimen = session.scalar(
            select(SpecimenRecord).where(SpecimenRecord.accession_no == accession_no)
        )
        if specimen is not None:
            return specimen
    if specimen_barcode:
        container = session.scalar(
            select(ContainerRecord).where(ContainerRecord.barcode == specimen_barcode)
        )
        if container is not None:
            return session.get(SpecimenRecord, container.specimen_id)
    return None


def _ensure_message_not_processed(
    session: Session,
    *,
    message_type: str,
    control_id: str,
) -> None:
    existing = session.scalar(
        select(InterfaceMessageLogRecord).where(
            InterfaceMessageLogRecord.protocol == "hl7v2",
            InterfaceMessageLogRecord.direction == "inbound",
            InterfaceMessageLogRecord.message_type == message_type,
            InterfaceMessageLogRecord.control_id == control_id,
            InterfaceMessageLogRecord.processed_ok.is_(True),
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="HL7 message with this control ID was already processed.",
        )


def _create_interface_message_log(
    session: Session,
    *,
    protocol: str,
    direction: str,
    message_type: str,
    payload: str,
    control_id: str | None = None,
    related_entity_type: str | None = None,
    related_entity_id: str | None = None,
    processed_ok: bool,
    error_text: str | None = None,
) -> InterfaceMessageLogRecord:
    message_log = InterfaceMessageLogRecord(
        id=str(uuid4()),
        protocol=protocol,
        direction=direction,
        message_type=message_type,
        control_id=control_id,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        payload=payload,
        processed_ok=processed_ok,
        error_text=error_text,
    )
    session.add(message_log)
    return message_log


def _create_raw_instrument_message(
    session: Session,
    *,
    device: DeviceRecord,
    protocol: str,
    direction: str,
    message_type: str | None,
    accession_no: str | None,
    specimen_barcode: str | None,
    payload: str,
    parsed_ok: bool,
    created_observation_count: int,
    parser_version: str = "device-gateway-v1",
) -> RawInstrumentMessageRecord:
    record = RawInstrumentMessageRecord(
        id=str(uuid4()),
        device_id=device.id,
        protocol=protocol,
        direction=direction,
        message_type=message_type,
        accession_no=accession_no,
        specimen_barcode=specimen_barcode,
        parser_version=parser_version,
        payload=payload,
        parsed_ok=parsed_ok,
        created_observation_count=created_observation_count,
    )
    session.add(record)
    return record


def _complete_related_task_if_any(session: Session, *, order_item_id: str, device_id: str) -> None:
    task = session.scalar(
        select(TaskRecord)
        .where(TaskRecord.based_on_order_item_id == order_item_id)
        .order_by(TaskRecord.authored_on.desc())
    )
    if task is None:
        return
    if task.device_id not in {None, device_id}:
        return
    if task.status not in {"ready", "in_progress", "on_hold"}:
        return
    task.status = "completed"
    task.device_id = device_id
    task.completed_at = datetime.now(UTC)


def _catalog_lookup_for_order_items(
    session: Session,
    order_items: list[OrderItemRecord],
) -> dict[str, TestCatalogRecord]:
    catalog_ids = {item.test_catalog_id for item in order_items}
    if not catalog_ids:
        return {}
    return {
        catalog.id: catalog
        for catalog in session.scalars(
            select(TestCatalogRecord).where(TestCatalogRecord.id.in_(catalog_ids))
        ).all()
    }


def _get_report_or_404(session: Session, report_id: UUID) -> DiagnosticReportRecord:
    report = session.get(DiagnosticReportRecord, str(report_id))
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} was not found.",
        )
    return report


def _get_order_or_404(session: Session, order_id: UUID) -> OrderRecord:
    order = session.get(OrderRecord, str(order_id))
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} was not found.",
        )
    return order


def _get_patient_or_404(session: Session, patient_id: UUID) -> PatientRecord:
    patient = session.get(PatientRecord, str(patient_id))
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} was not found.",
        )
    return patient


def _get_device_or_404(session: Session, device_id: UUID) -> DeviceRecord:
    device = session.get(DeviceRecord, str(device_id))
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} was not found.",
        )
    return device


def _get_catalog_or_404(session: Session, catalog_id: UUID) -> TestCatalogRecord:
    catalog = session.get(TestCatalogRecord, str(catalog_id))
    if catalog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog item {catalog_id} was not found.",
        )
    return catalog


def _first_specimen_barcode(session: Session, specimen_id: str) -> str | None:
    container = session.scalar(
        select(ContainerRecord)
        .where(ContainerRecord.specimen_id == specimen_id)
        .order_by(ContainerRecord.created_at.asc())
    )
    return container.barcode if container is not None else None


def _require_segment(message: HL7Message, segment_name: str, detail: str):
    segment = message.segment(segment_name)
    if segment is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
    return segment


def _log_hl7_failure(
    session: Session,
    raw_message: str,
    *,
    default_message_type: str,
    detail: str,
) -> None:
    control_id = None
    message_type = default_message_type
    try:
        message = parse_hl7_message(raw_message)
        control_id = message.control_id() or None
        message_type = message.message_type() or default_message_type
    except Exception:
        pass
    _create_interface_message_log(
        session,
        protocol="hl7v2",
        direction="inbound",
        message_type=message_type,
        control_id=control_id,
        payload=raw_message,
        processed_ok=False,
        error_text=detail,
    )
    session.commit()


def _hl7_priority_to_internal(value: str | None) -> str:
    lookup = {
        "S": "stat",
        "A": "asap",
        "R": "routine",
        "P": "routine",
        "T": "urgent",
    }
    return lookup.get((value or "").strip().upper(), "routine")


def _sex_from_hl7(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().upper()
    return {"M": "M", "F": "F", "O": "other", "U": "unknown"}.get(normalized, normalized)


def _parse_obx_value(
    hl7_value_type: str | None,
    raw_value: str | None,
) -> tuple[str, float | None, str | None, bool | None, str | None, str | None]:
    value_type_hl7 = (hl7_value_type or "ST").strip().upper()
    internal_value_type = {
        "NM": "quantity",
        "SN": "quantity",
        "ST": "text",
        "TX": "text",
        "FT": "text",
        "CE": "coded",
        "CWE": "coded",
        "CNE": "coded",
        "ID": "text",
        "IS": "text",
        "BOOL": "boolean",
    }.get(value_type_hl7, "text")

    value_num = None
    value_text = None
    value_boolean = None
    value_code_system = None
    value_code = None
    if internal_value_type == "quantity":
        try:
            value_num = float(raw_value) if raw_value not in {None, ""} else None
        except (TypeError, ValueError):
            internal_value_type = "text"
            value_text = raw_value
    elif internal_value_type == "coded":
        value_code, value_text, value_code_system = code_parts(raw_value)
    elif internal_value_type == "boolean":
        value_boolean = _bool_from_hl7(raw_value)
        if value_boolean is None:
            internal_value_type = "text"
            value_text = raw_value
    else:
        value_text = raw_value
    return (
        internal_value_type,
        value_num,
        value_text,
        value_boolean,
        value_code_system,
        value_code,
    )


def _bool_from_hl7(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    if normalized in {"Y", "YES", "T", "TRUE", "1"}:
        return True
    if normalized in {"N", "NO", "F", "FALSE", "0"}:
        return False
    return None


def _astm_status_to_internal(value: str | None) -> str:
    lookup = {
        "F": "final",
        "P": "preliminary",
        "C": "corrected",
        "X": "cancelled",
        "I": "registered",
    }
    return lookup.get((value or "").strip().upper(), "preliminary")


def _format_obx_value(observation: ObservationRecord) -> tuple[str, str, str]:
    if observation.value_type == "quantity":
        value = "" if observation.value_num is None else str(observation.value_num)
        return "NM", value, observation.unit_ucum or ""
    if observation.value_type == "coded":
        value = "^".join(
            [
                observation.value_code or "",
                observation.value_text or "",
                observation.value_code_system or "",
            ]
        )
        return "CE", value, ""
    if observation.value_type == "boolean":
        if observation.value_boolean is None:
            return "ID", observation.value_text or "", ""
        return "ID", "Y" if observation.value_boolean else "N", ""
    return "ST", observation.value_text or "", observation.unit_ucum or ""


def _generate_identifier(prefix: str) -> str:
    return f"{prefix}-{datetime.now(UTC):%Y%m%d%H%M%S}-{uuid4().hex[:8].upper()}"


def _to_patient_summary(patient: PatientRecord) -> PatientSummary:
    return PatientSummary(
        id=patient.id,
        mrn=patient.mrn,
        given_name=patient.given_name,
        family_name=patient.family_name,
        sex_code=patient.sex_code,
        birth_date=patient.birth_date,
        created_at=patient.created_at,
    )


def _to_order_summary(order: OrderRecord) -> OrderSummary:
    return OrderSummary(
        id=order.id,
        requisition_no=order.requisition_no,
        patient_id=order.patient_id,
        source_system=order.source_system,
        priority=order.priority,
        status=order.status,
        ordered_at=order.ordered_at,
    )


def _to_order_item_summary(item: OrderItemRecord) -> OrderItemSummary:
    return OrderItemSummary(
        id=item.id,
        order_id=item.order_id,
        line_no=item.line_no,
        test_catalog_id=item.test_catalog_id,
        requested_specimen_type_code=item.requested_specimen_type_code,
        status=item.status,
        priority=item.priority,
    )


def _to_specimen_summary(specimen: SpecimenRecord) -> SpecimenSummary:
    return SpecimenSummary(
        id=specimen.id,
        accession_no=specimen.accession_no,
        order_id=specimen.order_id,
        patient_id=specimen.patient_id,
        specimen_type_code=specimen.specimen_type_code,
        status=specimen.status,
        collected_at=specimen.collected_at,
        received_at=specimen.received_at,
    )


def _to_observation_summary(observation: ObservationRecord) -> ObservationSummary:
    return ObservationSummary(
        id=observation.id,
        order_item_id=observation.order_item_id,
        specimen_id=observation.specimen_id,
        raw_message_id=observation.raw_message_id,
        code_local=observation.code_local,
        code_loinc=observation.code_loinc,
        status=observation.status,
        category_code=observation.category_code,
        value_type=observation.value_type,
        value_num=observation.value_num,
        value_text=observation.value_text,
        value_boolean=observation.value_boolean,
        value_code_system=observation.value_code_system,
        value_code=observation.value_code,
        unit_ucum=observation.unit_ucum,
        interpretation_code=observation.interpretation_code,
        abnormal_flag=observation.abnormal_flag,
        method_code=observation.method_code,
        device_id=observation.device_id,
        effective_at=observation.effective_at,
        issued_at=observation.issued_at,
        reference_interval_snapshot=observation.reference_interval_snapshot,
    )


def _to_integrated_observation_summary(
    observation: ObservationRecord,
    autoverification: AutoverificationApplyResponse | None,
) -> IntegratedObservationSummary:
    return IntegratedObservationSummary(
        **_to_observation_summary(observation).model_dump(),
        autoverification=autoverification,
    )


def _to_interface_message_summary(message: InterfaceMessageLogRecord) -> InterfaceMessageSummary:
    return InterfaceMessageSummary(
        id=message.id,
        protocol=message.protocol,
        direction=message.direction,
        message_type=message.message_type,
        control_id=message.control_id,
        related_entity_type=message.related_entity_type,
        related_entity_id=message.related_entity_id,
        processed_ok=message.processed_ok,
        error_text=message.error_text,
        created_at=message.created_at,
    )


def _to_raw_message_summary(message: RawInstrumentMessageRecord) -> RawInstrumentMessageSummary:
    return RawInstrumentMessageSummary(
        id=message.id,
        device_id=message.device_id,
        protocol=message.protocol,
        direction=message.direction,
        message_type=message.message_type,
        accession_no=message.accession_no,
        specimen_barcode=message.specimen_barcode,
        parser_version=message.parser_version,
        parsed_ok=message.parsed_ok,
        parse_error=message.parse_error,
        created_observation_count=message.created_observation_count,
        created_at=message.created_at,
    )
