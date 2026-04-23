from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import (
    AnalyzerTransportFrameLogRecord,
    AnalyzerTransportMessageRecord,
    AnalyzerTransportProfileRecord,
    AnalyzerTransportSessionRecord,
    DeviceRecord,
)
from app.schemas.auth import UserSummary
from app.schemas.integrations import ASTMMessageImportRequest
from app.schemas.analyzer_transport import (
    AnalyzerTransportAckResponse,
    AnalyzerTransportConnectionMode,
    AnalyzerTransportDebugSnapshot,
    AnalyzerTransportDirection,
    AnalyzerTransportDispatchASTMRequest,
    AnalyzerTransportDispatchResponse,
    AnalyzerTransportEventKind,
    AnalyzerTransportFrameLogSummary,
    AnalyzerTransportFramePayload,
    AnalyzerTransportInboundControlResponse,
    AnalyzerTransportInboundFrameResponse,
    AnalyzerTransportItem,
    AnalyzerTransportLastSentKind,
    AnalyzerTransportListFramesResponse,
    AnalyzerTransportListMessagesResponse,
    AnalyzerTransportListProfilesResponse,
    AnalyzerTransportListSessionsResponse,
    AnalyzerTransportMessageActionResponse,
    AnalyzerTransportMessageStatus,
    AnalyzerTransportMessageSummary,
    AnalyzerTransportNextOutboundResponse,
    AnalyzerTransportParsedFrame,
    AnalyzerTransportProfileCreateRequest,
    AnalyzerTransportProfileSummary,
    AnalyzerTransportProtocol,
    AnalyzerTransportQueueOutboundRequest,
    AnalyzerTransportReceiveControlRequest,
    AnalyzerTransportReceiveFrameRequest,
    AnalyzerTransportRuntimeMetrics,
    AnalyzerTransportRuntimeOverview,
    AnalyzerTransportSessionCreateRequest,
    AnalyzerTransportSessionStatus,
    AnalyzerTransportSessionSummary,
)
from app.services import integrations as integration_service
from app.services.astm import build_astm_worklist
from app.services.audit import write_audit_event

STX = "\x02"
ETX = "\x03"
ETB = "\x17"
EOT = "\x04"
ENQ = "\x05"
ACK = "\x06"
NAK = "\x15"
CR = "\r"
LF = "\n"

CONTROL_MARKERS = {
    "<STX>": STX,
    "<ETX>": ETX,
    "<ETB>": ETB,
    "<EOT>": EOT,
    "<ENQ>": ENQ,
    "<ACK>": ACK,
    "<NAK>": NAK,
    "<CR>": CR,
    "<LF>": LF,
}
REVERSE_CONTROL_MARKERS = {value: key for key, value in CONTROL_MARKERS.items()}


def escape_transport_text(value: str) -> str:
    return "".join(REVERSE_CONTROL_MARKERS.get(char, char) for char in value)


def normalize_transport_text(value: str) -> str:
    text = value
    for marker, raw in CONTROL_MARKERS.items():
        text = text.replace(marker, raw)
    return text


def normalize_control_code(value: str | None) -> str:
    normalized = (value or "").strip().upper().replace("<", "").replace(">", "")
    if normalized not in {"ENQ", "ACK", "NAK", "EOT"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported control code: {value}",
        )
    return normalized


def next_astm_seq(current: int) -> int:
    return 1 if current >= 7 else current + 1


def astm_checksum(body: str) -> str:
    return f"{sum(ord(ch) for ch in body) % 256:02X}"


def frame_astm_message(
    payload: str,
    *,
    frame_payload_size: int = 240,
    starting_seq: int = 1,
) -> list[dict[str, str | int | bool]]:
    if frame_payload_size < 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="frame_payload_size must be at least 10.",
        )
    normalized_payload = normalize_transport_text(payload)
    chunks = [
        normalized_payload[index : index + frame_payload_size]
        for index in range(0, len(normalized_payload), frame_payload_size)
    ] or [""]
    frames: list[dict[str, str | int | bool]] = []
    seq = starting_seq
    for index, chunk in enumerate(chunks):
        is_final = index == len(chunks) - 1
        terminator = ETX if is_final else ETB
        body = f"{seq}{chunk}{terminator}"
        checksum = astm_checksum(body)
        framed_payload = f"{STX}{body}{checksum}{CR}{LF}"
        frames.append(
            {
                "frame_no": seq,
                "payload_chunk": chunk,
                "is_final": is_final,
                "checksum_hex": checksum,
                "framed_payload": framed_payload,
                "framed_payload_escaped": escape_transport_text(framed_payload),
            }
        )
        seq = next_astm_seq(seq)
    return frames


def parse_astm_frame(framed_payload: str) -> AnalyzerTransportParsedFrame:
    framed = normalize_transport_text(framed_payload)
    if not framed.startswith(STX):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Frame must start with STX.",
        )
    if not framed.endswith(CR + LF):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Frame must end with CRLF.",
        )

    content = framed[1:-2]
    if len(content) < 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Frame body is too short.",
        )

    checksum_hex = content[-2:].upper()
    body = content[:-2]
    if len(body) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Frame body is too short.",
        )

    terminator = body[-1]
    if terminator not in {ETX, ETB}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Frame must contain ETX or ETB terminator.",
        )
    frame_no_raw = body[0]
    if not frame_no_raw.isdigit():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ASTM frame number must be numeric.",
        )

    payload_chunk = body[1:-1]
    expected_checksum_hex = astm_checksum(body)
    return AnalyzerTransportParsedFrame(
        frame_no=int(frame_no_raw),
        payload_chunk=payload_chunk,
        is_final=terminator == ETX,
        checksum_hex=checksum_hex,
        expected_checksum_hex=expected_checksum_hex,
        checksum_ok=checksum_hex == expected_checksum_hex,
        framed_payload=framed,
        framed_payload_escaped=escape_transport_text(framed),
    )


def list_profiles(
    session: Session,
    *,
    device_id: UUID | None = None,
) -> AnalyzerTransportListProfilesResponse:
    stmt: Select[tuple[AnalyzerTransportProfileRecord]] = select(
        AnalyzerTransportProfileRecord
    ).order_by(AnalyzerTransportProfileRecord.created_at.desc())
    if device_id is not None:
        stmt = stmt.where(AnalyzerTransportProfileRecord.device_id == str(device_id))
    return AnalyzerTransportListProfilesResponse(
        items=[_to_profile_summary(row) for row in session.scalars(stmt).all()]
    )


def create_profile(
    session: Session,
    payload: AnalyzerTransportProfileCreateRequest,
    *,
    actor: UserSummary | None = None,
) -> AnalyzerTransportProfileSummary:
    device = _get_device_or_404(session, payload.device_id)
    _validate_transport_profile_payload(payload)
    existing_active = session.scalars(
        select(AnalyzerTransportProfileRecord).where(
            AnalyzerTransportProfileRecord.device_id == device.id,
            AnalyzerTransportProfileRecord.active.is_(True),
        )
    ).all()
    for record in existing_active:
        record.active = False

    profile = AnalyzerTransportProfileRecord(
        id=str(uuid4()),
        device_id=device.id,
        protocol=payload.protocol.value,
        framing_mode=payload.framing_mode.value,
        connection_mode=payload.connection_mode.value,
        tcp_host=payload.tcp_host,
        tcp_port=payload.tcp_port,
        serial_port=payload.serial_port,
        serial_baudrate=payload.serial_baudrate,
        frame_payload_size=payload.frame_payload_size,
        ack_timeout_seconds=payload.ack_timeout_seconds,
        max_retries=payload.max_retries,
        poll_interval_seconds=payload.poll_interval_seconds,
        read_timeout_seconds=payload.read_timeout_seconds,
        write_timeout_seconds=payload.write_timeout_seconds,
        auto_dispatch_astm=payload.auto_dispatch_astm,
        auto_verify=payload.auto_verify,
        active=payload.active,
    )
    session.add(profile)
    write_audit_event(
        session,
        entity_type="analyzer_transport_profile",
        entity_id=profile.id,
        action="create",
        status="active" if profile.active else "inactive",
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"device_id": device.id, "device_code": device.code},
    )
    session.commit()
    session.refresh(profile)
    return _to_profile_summary(profile)


def list_sessions(
    session: Session,
    *,
    device_id: UUID | None = None,
) -> AnalyzerTransportListSessionsResponse:
    stmt: Select[tuple[AnalyzerTransportSessionRecord]] = select(
        AnalyzerTransportSessionRecord
    ).order_by(AnalyzerTransportSessionRecord.created_at.desc())
    if device_id is not None:
        stmt = stmt.where(AnalyzerTransportSessionRecord.device_id == str(device_id))
    return AnalyzerTransportListSessionsResponse(
        items=[_to_session_summary(row) for row in session.scalars(stmt).all()]
    )


def get_runtime_overview(
    session: Session,
    *,
    device_id: UUID | None = None,
) -> AnalyzerTransportRuntimeOverview:
    profile_stmt: Select[tuple[AnalyzerTransportProfileRecord]] = select(
        AnalyzerTransportProfileRecord
    )
    session_stmt: Select[tuple[AnalyzerTransportSessionRecord]] = select(
        AnalyzerTransportSessionRecord
    ).order_by(AnalyzerTransportSessionRecord.last_activity_at.desc())
    if device_id is not None:
        profile_stmt = profile_stmt.where(AnalyzerTransportProfileRecord.device_id == str(device_id))
        session_stmt = session_stmt.where(AnalyzerTransportSessionRecord.device_id == str(device_id))

    profiles = session.scalars(profile_stmt).all()
    sessions = session.scalars(session_stmt).all()
    now = datetime.now(UTC)

    leased_session_count = sum(
        1
        for item in sessions
        if item.lease_owner is not None
        and _as_utc(item.lease_expires_at) is not None
        and _as_utc(item.lease_expires_at) > now
    )
    stale_lease_count = sum(
        1
        for item in sessions
        if item.lease_owner is not None
        and _as_utc(item.lease_expires_at) is not None
        and _as_utc(item.lease_expires_at) <= now
    )
    backoff_session_count = sum(
        1
        for item in sessions
        if _as_utc(item.next_retry_at) is not None and _as_utc(item.next_retry_at) > now
    )
    error_session_count = sum(1 for item in sessions if item.session_status == "error")

    return AnalyzerTransportRuntimeOverview(
        profile_count=len(profiles),
        session_count=len(sessions),
        leased_session_count=leased_session_count,
        stale_lease_count=stale_lease_count,
        backoff_session_count=backoff_session_count,
        error_session_count=error_session_count,
        items=[_to_session_summary(item) for item in sessions],
    )


def get_runtime_metrics(
    session: Session,
    *,
    device_id: UUID | None = None,
) -> AnalyzerTransportRuntimeMetrics:
    profile_stmt: Select[tuple[AnalyzerTransportProfileRecord]] = select(
        AnalyzerTransportProfileRecord
    )
    session_stmt: Select[tuple[AnalyzerTransportSessionRecord]] = select(
        AnalyzerTransportSessionRecord
    )
    message_stmt: Select[tuple[AnalyzerTransportMessageRecord]] = select(
        AnalyzerTransportMessageRecord
    )
    if device_id is not None:
        device_id_str = str(device_id)
        profile_stmt = profile_stmt.where(AnalyzerTransportProfileRecord.device_id == device_id_str)
        session_stmt = session_stmt.where(AnalyzerTransportSessionRecord.device_id == device_id_str)
        message_stmt = message_stmt.where(AnalyzerTransportMessageRecord.device_id == device_id_str)

    profiles = session.scalars(profile_stmt).all()
    sessions = session.scalars(session_stmt).all()
    messages = session.scalars(message_stmt).all()
    now = datetime.now(UTC)

    leased_session_count = sum(
        1
        for item in sessions
        if item.lease_owner is not None
        and _as_utc(item.lease_expires_at) is not None
        and _as_utc(item.lease_expires_at) > now
    )
    stale_lease_count = sum(
        1
        for item in sessions
        if item.lease_owner is not None
        and _as_utc(item.lease_expires_at) is not None
        and _as_utc(item.lease_expires_at) <= now
    )
    backoff_session_count = sum(
        1
        for item in sessions
        if _as_utc(item.next_retry_at) is not None and _as_utc(item.next_retry_at) > now
    )
    error_session_count = sum(1 for item in sessions if item.session_status == "error")
    active_outbound_session_count = sum(1 for item in sessions if item.outbound_message_id is not None)
    active_inbound_session_count = sum(1 for item in sessions if item.inbound_message_id is not None)

    status_counts: dict[str, int] = {}
    for message in messages:
        status_key = message.transport_status
        status_counts[status_key] = status_counts.get(status_key, 0) + 1

    return AnalyzerTransportRuntimeMetrics(
        profile_count=len(profiles),
        session_count=len(sessions),
        message_count=len(messages),
        leased_session_count=leased_session_count,
        stale_lease_count=stale_lease_count,
        backoff_session_count=backoff_session_count,
        error_session_count=error_session_count,
        active_outbound_session_count=active_outbound_session_count,
        active_inbound_session_count=active_inbound_session_count,
        queued_outbound_count=status_counts.get(AnalyzerTransportMessageStatus.QUEUED.value, 0),
        ready_outbound_count=status_counts.get(AnalyzerTransportMessageStatus.READY.value, 0),
        awaiting_ack_count=status_counts.get(AnalyzerTransportMessageStatus.AWAITING_ACK.value, 0),
        resend_count=status_counts.get(AnalyzerTransportMessageStatus.RESEND.value, 0),
        failed_message_count=status_counts.get(AnalyzerTransportMessageStatus.FAILED.value, 0),
        dead_letter_count=status_counts.get(AnalyzerTransportMessageStatus.DEAD_LETTER.value, 0),
        receiving_inbound_count=status_counts.get(AnalyzerTransportMessageStatus.RECEIVING.value, 0),
        received_inbound_count=status_counts.get(AnalyzerTransportMessageStatus.RECEIVED.value, 0),
        dispatched_count=status_counts.get(AnalyzerTransportMessageStatus.DISPATCHED.value, 0),
        completed_outbound_count=status_counts.get(AnalyzerTransportMessageStatus.COMPLETED.value, 0),
        status_counts=status_counts,
    )


def create_session(
    session: Session,
    payload: AnalyzerTransportSessionCreateRequest,
    *,
    actor: UserSummary | None = None,
) -> AnalyzerTransportSessionSummary:
    device = _get_device_or_404(session, payload.device_id)
    profile = _ensure_transport_profile(session, profile_id=payload.profile_id, device_id=payload.device_id)
    transport_session = AnalyzerTransportSessionRecord(
        id=str(uuid4()),
        device_id=device.id,
        profile_id=profile.id,
        session_status=AnalyzerTransportSessionStatus.IDLE.value,
        expected_inbound_frame_no=1,
        last_activity_at=datetime.now(UTC),
    )
    session.add(transport_session)
    write_audit_event(
        session,
        entity_type="analyzer_transport_session",
        entity_id=transport_session.id,
        action="open",
        status="idle",
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"device_id": device.id, "profile_id": profile.id},
    )
    session.commit()
    session.refresh(transport_session)
    return _to_session_summary(transport_session)


def get_session(
    session: Session,
    session_id: UUID,
) -> AnalyzerTransportSessionSummary:
    return _to_session_summary(_get_transport_session_or_404(session, session_id))


def list_messages(
    session: Session,
    *,
    session_id: UUID,
) -> AnalyzerTransportListMessagesResponse:
    transport_session = _get_transport_session_or_404(session, session_id)
    stmt: Select[tuple[AnalyzerTransportMessageRecord]] = select(
        AnalyzerTransportMessageRecord
    ).where(AnalyzerTransportMessageRecord.session_id == transport_session.id).order_by(
        AnalyzerTransportMessageRecord.created_at.desc()
    )
    return AnalyzerTransportListMessagesResponse(
        items=[_to_message_summary(row) for row in session.scalars(stmt).all()]
    )


def list_frames(
    session: Session,
    *,
    session_id: UUID,
    message_id: UUID | None = None,
) -> AnalyzerTransportListFramesResponse:
    transport_session = _get_transport_session_or_404(session, session_id)
    stmt: Select[tuple[AnalyzerTransportFrameLogRecord]] = select(
        AnalyzerTransportFrameLogRecord
    ).where(AnalyzerTransportFrameLogRecord.session_id == transport_session.id)
    if message_id is not None:
        stmt = stmt.where(AnalyzerTransportFrameLogRecord.message_id == str(message_id))
    stmt = stmt.order_by(AnalyzerTransportFrameLogRecord.created_at.asc())
    return AnalyzerTransportListFramesResponse(
        items=[_to_frame_log_summary(row) for row in session.scalars(stmt).all()]
    )


def queue_outbound_message(
    session: Session,
    *,
    session_id: UUID,
    payload: AnalyzerTransportQueueOutboundRequest,
    actor: UserSummary | None = None,
) -> AnalyzerTransportMessageSummary:
    transport_session = _get_transport_session_or_404(session, session_id)
    profile = _ensure_transport_profile(
        session,
        profile_id=UUID(transport_session.profile_id),
        device_id=UUID(transport_session.device_id),
    )
    frames = frame_astm_message(
        payload.logical_payload,
        frame_payload_size=profile.frame_payload_size,
    )
    message = AnalyzerTransportMessageRecord(
        id=str(uuid4()),
        session_id=transport_session.id,
        device_id=transport_session.device_id,
        direction=AnalyzerTransportDirection.OUTBOUND.value,
        protocol=payload.protocol.value,
        message_type=payload.message_type,
        transport_status=AnalyzerTransportMessageStatus.QUEUED.value,
        logical_payload=normalize_transport_text(payload.logical_payload),
        frames_payload=frames,
        total_frames=len(frames),
        next_frame_index=0,
        retry_count=0,
        correlation_key=payload.correlation_key,
    )
    session.add(message)
    session.flush()
    _touch_transport_session(
        transport_session,
        session_status=AnalyzerTransportSessionStatus.SENDING,
    )
    write_audit_event(
        session,
        entity_type="analyzer_transport_message",
        entity_id=message.id,
        action="queue-outbound",
        status="queued",
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={
            "session_id": transport_session.id,
            "device_id": transport_session.device_id,
            "message_type": message.message_type,
        },
    )
    session.commit()
    session.refresh(message)
    return _to_message_summary(message)


def queue_astm_worklist(
    session: Session,
    *,
    session_id: UUID,
    actor: UserSummary | None = None,
) -> AnalyzerTransportDebugSnapshot:
    transport_session = _get_transport_session_or_404(session, session_id)
    device = _get_device_or_404(session, UUID(transport_session.device_id))
    worklist = integration_service.get_device_worklist(session, UUID(device.id))
    worklist_payload = build_astm_worklist(
        device.code,
        [item.model_dump(mode="json") for item in worklist.items],
    )
    message = queue_outbound_message(
        session,
        session_id=session_id,
        payload=AnalyzerTransportQueueOutboundRequest(
            protocol=AnalyzerTransportProtocol.ASTM_TRANSPORT,
            message_type="ASTM-WORKLIST",
            logical_payload=worklist_payload,
            correlation_key=device.code,
        ),
        actor=actor,
    )
    refreshed_session = _get_transport_session_or_404(session, session_id)
    return AnalyzerTransportDebugSnapshot(
        session=_to_session_summary(refreshed_session),
        message=message,
        extra={"worklist_items": len(worklist.items)},
    )


def next_outbound_transport_item(
    session: Session,
    *,
    session_id: UUID,
) -> AnalyzerTransportNextOutboundResponse:
    transport_session = _get_transport_session_or_404(session, session_id)
    message = _active_or_next_outbound_message(session, transport_session)
    if message is None:
        return AnalyzerTransportNextOutboundResponse(
            session=_to_session_summary(transport_session),
            message=None,
            transport_item=None,
            awaiting_ack=False,
            ack_timeout_seconds=None,
        )

    profile = _ensure_transport_profile(
        session,
        profile_id=UUID(transport_session.profile_id),
        device_id=UUID(transport_session.device_id),
    )
    deadline = _ack_deadline(profile)

    if message.transport_status == AnalyzerTransportMessageStatus.AWAITING_ACK.value:
        return AnalyzerTransportNextOutboundResponse(
            session=_to_session_summary(transport_session),
            message=_to_message_summary(message),
            transport_item=_build_current_transport_item(message),
            awaiting_ack=True,
            ack_timeout_seconds=profile.ack_timeout_seconds,
        )

    transport_item: AnalyzerTransportItem
    if (
        message.transport_status == AnalyzerTransportMessageStatus.RESEND.value
        and message.last_sent_kind in {kind.value for kind in AnalyzerTransportLastSentKind}
    ):
        message.transport_status = AnalyzerTransportMessageStatus.AWAITING_ACK.value
        message.ack_deadline_at = deadline
        _touch_transport_session(
            transport_session,
            session_status=AnalyzerTransportSessionStatus.AWAITING_ACK,
        )
        transport_item = _build_current_transport_item(message)
        _log_resend(session, transport_session, message, transport_item)
    elif message.transport_status == AnalyzerTransportMessageStatus.QUEUED.value:
        message.transport_status = AnalyzerTransportMessageStatus.AWAITING_ACK.value
        message.last_sent_kind = AnalyzerTransportLastSentKind.ENQ.value
        message.pending_frame_index = None
        message.ack_deadline_at = deadline
        _touch_transport_session(
            transport_session,
            session_status=AnalyzerTransportSessionStatus.AWAITING_ACK,
        )
        transport_item = AnalyzerTransportItem(
            kind="control",
            control_code="ENQ",
            payload=ENQ,
            payload_escaped=escape_transport_text(ENQ),
            retry_count=message.retry_count,
        )
        _log_frame(
            session,
            session_id=transport_session.id,
            message_id=message.id,
            direction=AnalyzerTransportDirection.OUTBOUND,
            event_kind=AnalyzerTransportEventKind.CONTROL,
            control_code="ENQ",
            framed_payload=ENQ,
            retry_no=message.retry_count,
        )
    elif message.transport_status == AnalyzerTransportMessageStatus.READY.value:
        frames = message.frames_payload or []
        if message.next_frame_index < len(frames):
            frame = frames[message.next_frame_index]
            message.transport_status = AnalyzerTransportMessageStatus.AWAITING_ACK.value
            message.pending_frame_index = message.next_frame_index
            message.last_sent_kind = AnalyzerTransportLastSentKind.FRAME.value
            message.ack_deadline_at = deadline
            _touch_transport_session(
                transport_session,
                session_status=AnalyzerTransportSessionStatus.AWAITING_ACK,
            )
            transport_item = AnalyzerTransportItem(
                kind="frame",
                frame_no=int(frame["frame_no"]),
                payload=str(frame["framed_payload"]),
                payload_escaped=str(frame["framed_payload_escaped"]),
                is_final=bool(frame["is_final"]),
                checksum_hex=str(frame["checksum_hex"]),
                retry_count=message.retry_count,
            )
            _log_frame(
                session,
                session_id=transport_session.id,
                message_id=message.id,
                direction=AnalyzerTransportDirection.OUTBOUND,
                event_kind=AnalyzerTransportEventKind.FRAME,
                frame_no=int(frame["frame_no"]),
                payload_chunk=str(frame["payload_chunk"]),
                framed_payload=str(frame["framed_payload"]),
                checksum_hex=str(frame["checksum_hex"]),
                is_final=bool(frame["is_final"]),
                retry_no=message.retry_count,
            )
        else:
            message.transport_status = AnalyzerTransportMessageStatus.AWAITING_ACK.value
            message.pending_frame_index = None
            message.last_sent_kind = AnalyzerTransportLastSentKind.EOT.value
            message.ack_deadline_at = deadline
            _touch_transport_session(
                transport_session,
                session_status=AnalyzerTransportSessionStatus.AWAITING_ACK,
            )
            transport_item = AnalyzerTransportItem(
                kind="control",
                control_code="EOT",
                payload=EOT,
                payload_escaped=escape_transport_text(EOT),
                retry_count=message.retry_count,
            )
            _log_frame(
                session,
                session_id=transport_session.id,
                message_id=message.id,
                direction=AnalyzerTransportDirection.OUTBOUND,
                event_kind=AnalyzerTransportEventKind.CONTROL,
                control_code="EOT",
                framed_payload=EOT,
                retry_no=message.retry_count,
            )
    else:
        return AnalyzerTransportNextOutboundResponse(
            session=_to_session_summary(transport_session),
            message=_to_message_summary(message),
            transport_item=None,
            awaiting_ack=False,
            ack_timeout_seconds=profile.ack_timeout_seconds,
        )

    session.commit()
    session.refresh(transport_session)
    session.refresh(message)
    return AnalyzerTransportNextOutboundResponse(
        session=_to_session_summary(transport_session),
        message=_to_message_summary(message),
        transport_item=transport_item,
        awaiting_ack=False,
        ack_timeout_seconds=profile.ack_timeout_seconds,
    )


def acknowledge_outbound(
    session: Session,
    *,
    session_id: UUID,
    positive: bool,
    actor: UserSummary | None = None,
    notes: str | None = None,
) -> AnalyzerTransportAckResponse:
    transport_session = _get_transport_session_or_404(session, session_id)
    message = _active_or_next_outbound_message(session, transport_session)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active outbound transport message.",
        )
    if message.transport_status != AnalyzerTransportMessageStatus.AWAITING_ACK.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Outbound message is not awaiting ACK/NAK.",
        )
    if not positive:
        return _handle_negative_ack(
            session,
            transport_session=transport_session,
            message=message,
            reason="NAK",
            actor=actor,
            notes=notes,
        )

    _log_frame(
        session,
        session_id=transport_session.id,
        message_id=message.id,
        direction=AnalyzerTransportDirection.INBOUND,
        event_kind=AnalyzerTransportEventKind.CONTROL,
        control_code="ACK",
        framed_payload=ACK,
        retry_no=message.retry_count,
        notes=notes,
    )
    if message.last_sent_kind == AnalyzerTransportLastSentKind.ENQ.value:
        message.transport_status = AnalyzerTransportMessageStatus.READY.value
        message.pending_frame_index = None
        message.last_sent_kind = None
        message.ack_deadline_at = None
        _touch_transport_session(
            transport_session,
            session_status=AnalyzerTransportSessionStatus.SENDING,
        )
    elif message.last_sent_kind == AnalyzerTransportLastSentKind.FRAME.value:
        message.transport_status = AnalyzerTransportMessageStatus.READY.value
        message.next_frame_index = (message.pending_frame_index or 0) + 1
        message.pending_frame_index = None
        message.last_sent_kind = None
        message.ack_deadline_at = None
        message.retry_count = 0
        _touch_transport_session(
            transport_session,
            session_status=AnalyzerTransportSessionStatus.SENDING,
        )
    elif message.last_sent_kind == AnalyzerTransportLastSentKind.EOT.value:
        message.transport_status = AnalyzerTransportMessageStatus.COMPLETED.value
        message.pending_frame_index = None
        message.last_sent_kind = None
        message.ack_deadline_at = None
        message.retry_count = 0
        message.completed_at = datetime.now(UTC)
        _touch_transport_session(
            transport_session,
            session_status=AnalyzerTransportSessionStatus.IDLE,
            outbound_message_id=None,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unsupported outbound state for ACK.",
        )

    write_audit_event(
        session,
        entity_type="analyzer_transport_message",
        entity_id=message.id,
        action="outbound-ack",
        status=message.transport_status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"session_id": transport_session.id, "notes": notes},
    )
    session.commit()
    session.refresh(transport_session)
    session.refresh(message)
    return AnalyzerTransportAckResponse(
        decision="acknowledged",
        message=_to_message_summary(message),
        session=_to_session_summary(transport_session),
    )


def timeout_outbound(
    session: Session,
    *,
    session_id: UUID,
    actor: UserSummary | None = None,
    notes: str | None = None,
) -> AnalyzerTransportAckResponse:
    transport_session = _get_transport_session_or_404(session, session_id)
    message = _active_or_next_outbound_message(session, transport_session)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active outbound transport message.",
        )
    if message.transport_status != AnalyzerTransportMessageStatus.AWAITING_ACK.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Outbound message is not awaiting ACK/NAK.",
        )
    return _handle_negative_ack(
        session,
        transport_session=transport_session,
        message=message,
        reason="TIMEOUT",
        actor=actor,
        notes=notes,
    )


def receive_transport_control(
    session: Session,
    *,
    session_id: UUID,
    payload: AnalyzerTransportReceiveControlRequest,
    actor: UserSummary | None = None,
) -> AnalyzerTransportInboundControlResponse:
    transport_session = _get_transport_session_or_404(session, session_id)
    control_code = normalize_control_code(payload.control_code)

    if control_code in {"ACK", "NAK"}:
        ack = acknowledge_outbound(
            session,
            session_id=session_id,
            positive=control_code == "ACK",
            actor=actor,
            notes=f"inbound-{control_code.lower()}",
        )
        return AnalyzerTransportInboundControlResponse(
            reply_control_code=None,
            reply_payload=None,
            reply_payload_escaped=None,
            session=ack.session,
            message=ack.message,
        )

    if control_code == "ENQ":
        inbound_id = transport_session.inbound_message_id
        if inbound_id:
            existing = session.get(AnalyzerTransportMessageRecord, inbound_id)
            if existing is not None and existing.transport_status == AnalyzerTransportMessageStatus.RECEIVING.value:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Inbound transport message is already in progress.",
                )

        message = AnalyzerTransportMessageRecord(
            id=str(uuid4()),
            session_id=transport_session.id,
            device_id=transport_session.device_id,
            direction=AnalyzerTransportDirection.INBOUND.value,
            protocol="astm-transport",
            message_type="ASTM-INBOUND",
            transport_status=AnalyzerTransportMessageStatus.RECEIVING.value,
            logical_payload="",
            frames_payload=[],
            total_frames=0,
            next_frame_index=0,
        )
        session.add(message)
        session.flush()
        _touch_transport_session(
            transport_session,
            session_status=AnalyzerTransportSessionStatus.RECEIVING,
            inbound_message_id=message.id,
            expected_inbound_frame_no=1,
        )
        _log_frame(
            session,
            session_id=transport_session.id,
            message_id=message.id,
            direction=AnalyzerTransportDirection.INBOUND,
            event_kind=AnalyzerTransportEventKind.CONTROL,
            control_code="ENQ",
            framed_payload=ENQ,
        )
        write_audit_event(
            session,
            entity_type="analyzer_transport_session",
            entity_id=transport_session.id,
            action="inbound-enq",
            status="receiving",
            actor_user_id=str(actor.id) if actor else None,
            actor_username=actor.username if actor else None,
            actor_role_code=actor.role_code.value if actor else None,
            context={"message_id": message.id},
        )
        session.commit()
        session.refresh(transport_session)
        session.refresh(message)
        return AnalyzerTransportInboundControlResponse(
            reply_control_code="ACK",
            reply_payload=ACK,
            reply_payload_escaped=escape_transport_text(ACK),
            session=_to_session_summary(transport_session),
            message=_to_message_summary(message),
        )

    current_message = (
        session.get(AnalyzerTransportMessageRecord, transport_session.inbound_message_id)
        if transport_session.inbound_message_id
        else None
    )
    _log_frame(
        session,
        session_id=transport_session.id,
        message_id=current_message.id if current_message else None,
        direction=AnalyzerTransportDirection.INBOUND,
        event_kind=AnalyzerTransportEventKind.CONTROL,
        control_code="EOT",
        framed_payload=EOT,
    )
    if current_message is not None:
        if current_message.assembled_payload:
            current_message.transport_status = AnalyzerTransportMessageStatus.RECEIVED.value
            current_message.completed_at = datetime.now(UTC)
        else:
            current_message.transport_status = AnalyzerTransportMessageStatus.FAILED.value
            current_message.parse_error = "EOT before complete final frame."
            current_message.completed_at = datetime.now(UTC)

    _touch_transport_session(
        transport_session,
        session_status=AnalyzerTransportSessionStatus.IDLE,
        inbound_message_id=None,
        expected_inbound_frame_no=1,
    )
    write_audit_event(
        session,
        entity_type="analyzer_transport_session",
        entity_id=transport_session.id,
        action="inbound-eot",
        status=transport_session.session_status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"message_id": current_message.id if current_message else None},
    )
    session.commit()
    session.refresh(transport_session)
    if current_message is not None:
        session.refresh(current_message)
    return AnalyzerTransportInboundControlResponse(
        reply_control_code=None,
        reply_payload=None,
        reply_payload_escaped=None,
        session=_to_session_summary(transport_session),
        message=_to_message_summary(current_message) if current_message else None,
    )


def receive_transport_frame(
    session: Session,
    *,
    session_id: UUID,
    payload: AnalyzerTransportReceiveFrameRequest,
    actor: UserSummary | None = None,
) -> AnalyzerTransportInboundFrameResponse:
    transport_session = _get_transport_session_or_404(session, session_id)
    if not transport_session.inbound_message_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No inbound transport message in progress. Send ENQ first.",
        )
    message = _get_transport_message_or_404(session, UUID(transport_session.inbound_message_id))

    try:
        parsed = parse_astm_frame(payload.framed_payload)
    except HTTPException as exc:
        _log_frame(
            session,
            session_id=transport_session.id,
            message_id=message.id,
            direction=AnalyzerTransportDirection.INBOUND,
            event_kind=AnalyzerTransportEventKind.FRAME,
            framed_payload=normalize_transport_text(payload.framed_payload),
            accepted=False,
            notes=str(exc.detail),
        )
        session.commit()
        return AnalyzerTransportInboundFrameResponse(
            reply_control_code="NAK",
            reply_payload=NAK,
            reply_payload_escaped=escape_transport_text(NAK),
            accepted=False,
            duplicate=False,
            assembled=False,
            error=str(exc.detail),
            session=_to_session_summary(transport_session),
            message=_to_message_summary(message),
        )

    if not parsed.checksum_ok:
        _log_frame(
            session,
            session_id=transport_session.id,
            message_id=message.id,
            direction=AnalyzerTransportDirection.INBOUND,
            event_kind=AnalyzerTransportEventKind.FRAME,
            frame_no=parsed.frame_no,
            payload_chunk=parsed.payload_chunk,
            framed_payload=parsed.framed_payload,
            checksum_hex=parsed.checksum_hex,
            is_final=parsed.is_final,
            accepted=False,
            notes="checksum-mismatch",
        )
        session.commit()
        return AnalyzerTransportInboundFrameResponse(
            reply_control_code="NAK",
            reply_payload=NAK,
            reply_payload_escaped=escape_transport_text(NAK),
            accepted=False,
            duplicate=False,
            assembled=False,
            error="Checksum mismatch.",
            session=_to_session_summary(transport_session),
            message=_to_message_summary(message),
            parsed_frame=parsed,
        )

    duplicate = session.scalar(
        select(AnalyzerTransportFrameLogRecord.id).where(
            AnalyzerTransportFrameLogRecord.session_id == transport_session.id,
            AnalyzerTransportFrameLogRecord.message_id == message.id,
            AnalyzerTransportFrameLogRecord.direction == AnalyzerTransportDirection.INBOUND.value,
            AnalyzerTransportFrameLogRecord.event_kind == AnalyzerTransportEventKind.FRAME.value,
            AnalyzerTransportFrameLogRecord.framed_payload == parsed.framed_payload,
            AnalyzerTransportFrameLogRecord.accepted.is_(True),
        )
    )
    if duplicate is not None:
        _log_frame(
            session,
            session_id=transport_session.id,
            message_id=message.id,
            direction=AnalyzerTransportDirection.INBOUND,
            event_kind=AnalyzerTransportEventKind.FRAME,
            frame_no=parsed.frame_no,
            payload_chunk=parsed.payload_chunk,
            framed_payload=parsed.framed_payload,
            checksum_hex=parsed.checksum_hex,
            is_final=parsed.is_final,
            duplicate_flag=True,
            notes="duplicate-frame",
        )
        session.commit()
        return AnalyzerTransportInboundFrameResponse(
            reply_control_code="ACK",
            reply_payload=ACK,
            reply_payload_escaped=escape_transport_text(ACK),
            accepted=True,
            duplicate=True,
            assembled=False,
            session=_to_session_summary(transport_session),
            message=_to_message_summary(message),
            parsed_frame=parsed,
        )

    expected_seq = transport_session.expected_inbound_frame_no or 1
    if parsed.frame_no != expected_seq:
        _log_frame(
            session,
            session_id=transport_session.id,
            message_id=message.id,
            direction=AnalyzerTransportDirection.INBOUND,
            event_kind=AnalyzerTransportEventKind.FRAME,
            frame_no=parsed.frame_no,
            payload_chunk=parsed.payload_chunk,
            framed_payload=parsed.framed_payload,
            checksum_hex=parsed.checksum_hex,
            is_final=parsed.is_final,
            accepted=False,
            notes=f"unexpected-seq-expected-{expected_seq}",
        )
        session.commit()
        return AnalyzerTransportInboundFrameResponse(
            reply_control_code="NAK",
            reply_payload=NAK,
            reply_payload_escaped=escape_transport_text(NAK),
            accepted=False,
            duplicate=False,
            assembled=False,
            error=f"Unexpected frame number {parsed.frame_no}; expected {expected_seq}.",
            session=_to_session_summary(transport_session),
            message=_to_message_summary(message),
            parsed_frame=parsed,
        )

    message.logical_payload = f"{message.logical_payload}{parsed.payload_chunk}"
    message.total_frames = (message.total_frames or 0) + 1
    if parsed.is_final:
        message.assembled_payload = message.logical_payload
        message.transport_status = AnalyzerTransportMessageStatus.RECEIVED.value
    _touch_transport_session(
        transport_session,
        session_status=AnalyzerTransportSessionStatus.RECEIVING,
        expected_inbound_frame_no=next_astm_seq(parsed.frame_no),
    )
    _log_frame(
        session,
        session_id=transport_session.id,
        message_id=message.id,
        direction=AnalyzerTransportDirection.INBOUND,
        event_kind=AnalyzerTransportEventKind.FRAME,
        frame_no=parsed.frame_no,
        payload_chunk=parsed.payload_chunk,
        framed_payload=parsed.framed_payload,
        checksum_hex=parsed.checksum_hex,
        is_final=parsed.is_final,
    )

    dispatch_response = None
    if payload.auto_dispatch_astm and parsed.is_final:
        session.flush()
        dispatch_response = _dispatch_astm_message(
            session,
            message=message,
            auto_verify=payload.auto_verify,
            actor=actor,
        )

    session.commit()
    session.refresh(transport_session)
    session.refresh(message)
    return AnalyzerTransportInboundFrameResponse(
        reply_control_code="ACK",
        reply_payload=ACK,
        reply_payload_escaped=escape_transport_text(ACK),
        accepted=True,
        duplicate=False,
        assembled=parsed.is_final,
        session=_to_session_summary(transport_session),
        message=_to_message_summary(message),
        parsed_frame=parsed,
        dispatch=dispatch_response.dispatch if dispatch_response else None,
    )


def dispatch_astm_message(
    session: Session,
    *,
    message_id: UUID,
    payload: AnalyzerTransportDispatchASTMRequest,
    actor: UserSummary | None = None,
) -> AnalyzerTransportDispatchResponse:
    message = _get_transport_message_or_404(session, message_id)
    return _dispatch_astm_message(
        session,
        message=message,
        auto_verify=payload.auto_verify,
        actor=actor,
    )


def dead_letter_message(
    session: Session,
    *,
    message_id: UUID,
    actor: UserSummary | None = None,
    notes: str | None = None,
) -> AnalyzerTransportMessageActionResponse:
    message = _get_transport_message_or_404(session, message_id)
    transport_session = _get_transport_session_or_404(session, UUID(message.session_id))
    if message.transport_status in {
        AnalyzerTransportMessageStatus.COMPLETED.value,
        AnalyzerTransportMessageStatus.DISPATCHED.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Completed or dispatched transport messages cannot be dead-lettered.",
        )
    if message.transport_status == AnalyzerTransportMessageStatus.DEAD_LETTER.value:
        return AnalyzerTransportMessageActionResponse(
            action="dead_letter",
            session=_to_session_summary(transport_session),
            message=_to_message_summary(message),
        )

    message.transport_status = AnalyzerTransportMessageStatus.DEAD_LETTER.value
    message.ack_deadline_at = None
    message.pending_frame_index = None
    message.last_sent_kind = None
    message.completed_at = message.completed_at or datetime.now(UTC)
    message.parse_error = _merge_transport_error(message.parse_error, notes)

    if transport_session.outbound_message_id == message.id:
        _touch_transport_session(
            transport_session,
            session_status=_derive_session_status(
                transport_session,
                outbound_message_id=None,
                inbound_message_id=transport_session.inbound_message_id,
            ),
            outbound_message_id=None,
            last_error=notes or message.parse_error or "dead-lettered",
        )
    elif transport_session.inbound_message_id == message.id:
        _touch_transport_session(
            transport_session,
            session_status=_derive_session_status(
                transport_session,
                outbound_message_id=transport_session.outbound_message_id,
                inbound_message_id=None,
            ),
            inbound_message_id=None,
            expected_inbound_frame_no=1,
            last_error=notes or message.parse_error or "dead-lettered",
        )
    elif transport_session.outbound_message_id is None and transport_session.inbound_message_id is None:
        _touch_transport_session(
            transport_session,
            session_status=AnalyzerTransportSessionStatus.IDLE,
            last_error=notes or message.parse_error or "dead-lettered",
        )

    write_audit_event(
        session,
        entity_type="analyzer_transport_message",
        entity_id=message.id,
        action="dead-letter",
        status=message.transport_status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"session_id": transport_session.id, "notes": notes},
    )
    session.commit()
    session.refresh(transport_session)
    session.refresh(message)
    return AnalyzerTransportMessageActionResponse(
        action="dead_letter",
        session=_to_session_summary(transport_session),
        message=_to_message_summary(message),
    )


def requeue_message(
    session: Session,
    *,
    message_id: UUID,
    actor: UserSummary | None = None,
    notes: str | None = None,
) -> AnalyzerTransportMessageActionResponse:
    message = _get_transport_message_or_404(session, message_id)
    transport_session = _get_transport_session_or_404(session, UUID(message.session_id))

    if message.direction == AnalyzerTransportDirection.OUTBOUND.value:
        if message.transport_status not in {
            AnalyzerTransportMessageStatus.FAILED.value,
            AnalyzerTransportMessageStatus.DEAD_LETTER.value,
        }:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only failed or dead-letter outbound messages can be requeued.",
            )

        message.transport_status = AnalyzerTransportMessageStatus.QUEUED.value
        message.next_frame_index = 0
        message.pending_frame_index = None
        message.last_sent_kind = None
        message.retry_count = 0
        message.ack_deadline_at = None
        message.completed_at = None
        message.parse_error = None

        outbound_message_id = transport_session.outbound_message_id or message.id
        _touch_transport_session(
            transport_session,
            session_status=_derive_session_status(
                transport_session,
                outbound_message_id=outbound_message_id,
                inbound_message_id=transport_session.inbound_message_id,
            ),
            outbound_message_id=outbound_message_id,
            last_error=None,
        )
    else:
        if message.transport_status not in {
            AnalyzerTransportMessageStatus.FAILED.value,
            AnalyzerTransportMessageStatus.DEAD_LETTER.value,
            AnalyzerTransportMessageStatus.RECEIVED.value,
        }:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only failed, dead-letter, or received inbound messages can be requeued.",
            )
        if not (message.assembled_payload or message.logical_payload):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Inbound transport message has no assembled payload to replay.",
            )

        message.transport_status = AnalyzerTransportMessageStatus.RECEIVED.value
        message.parse_error = None

        if transport_session.inbound_message_id == message.id:
            _touch_transport_session(
                transport_session,
                session_status=_derive_session_status(
                    transport_session,
                    outbound_message_id=transport_session.outbound_message_id,
                    inbound_message_id=None,
                ),
                inbound_message_id=None,
                expected_inbound_frame_no=1,
                last_error=None,
            )

    write_audit_event(
        session,
        entity_type="analyzer_transport_message",
        entity_id=message.id,
        action="requeue",
        status=message.transport_status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"session_id": transport_session.id, "notes": notes},
    )
    session.commit()
    session.refresh(transport_session)
    session.refresh(message)
    return AnalyzerTransportMessageActionResponse(
        action="requeue",
        session=_to_session_summary(transport_session),
        message=_to_message_summary(message),
    )


def _dispatch_astm_message(
    session: Session,
    *,
    message: AnalyzerTransportMessageRecord,
    auto_verify: bool,
    actor: UserSummary | None = None,
) -> AnalyzerTransportDispatchResponse:
    if message.direction != AnalyzerTransportDirection.INBOUND.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only inbound transport messages can be dispatched.",
        )
    if message.protocol not in {
        AnalyzerTransportProtocol.ASTM_TRANSPORT.value,
        "astm",
    }:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only ASTM transport messages are supported.",
        )
    assembled_payload = message.assembled_payload or message.logical_payload
    if not assembled_payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transport message is not assembled yet.",
        )

    session.flush()
    dispatch = integration_service.import_astm_results(
        session,
        ASTMMessageImportRequest(
            device_id=UUID(message.device_id),
            message=assembled_payload,
            auto_verify=auto_verify,
        ),
        actor_user_id=str(actor.id) if actor else None,
    )

    message.transport_status = AnalyzerTransportMessageStatus.DISPATCHED.value
    message.dispatched_entity_type = "raw_instrument_message"
    message.dispatched_entity_id = str(dispatch.raw_message_id)
    message.completed_at = message.completed_at or datetime.now(UTC)
    write_audit_event(
        session,
        entity_type="analyzer_transport_message",
        entity_id=message.id,
        action="dispatch-astm",
        status="dispatched",
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={
            "raw_message_id": str(dispatch.raw_message_id),
            "device_id": message.device_id,
            "auto_verify": auto_verify,
        },
    )
    session.commit()
    session.refresh(message)
    return AnalyzerTransportDispatchResponse(
        message=_to_message_summary(message),
        dispatch=dispatch,
    )


def _handle_negative_ack(
    session: Session,
    *,
    transport_session: AnalyzerTransportSessionRecord,
    message: AnalyzerTransportMessageRecord,
    reason: str,
    actor: UserSummary | None = None,
    notes: str | None = None,
) -> AnalyzerTransportAckResponse:
    profile = _ensure_transport_profile(
        session,
        profile_id=UUID(transport_session.profile_id),
        device_id=UUID(transport_session.device_id),
    )
    message.retry_count = (message.retry_count or 0) + 1
    _log_frame(
        session,
        session_id=transport_session.id,
        message_id=message.id,
        direction=AnalyzerTransportDirection.INBOUND,
        event_kind=AnalyzerTransportEventKind.CONTROL,
        control_code=reason,
        framed_payload=NAK if reason == "NAK" else None,
        retry_no=message.retry_count,
        notes=notes,
    )

    if message.retry_count > profile.max_retries:
        message.transport_status = AnalyzerTransportMessageStatus.FAILED.value
        message.ack_deadline_at = None
        message.completed_at = datetime.now(UTC)
        message.parse_error = notes or reason
        _touch_transport_session(
            transport_session,
            session_status=AnalyzerTransportSessionStatus.ERROR,
            outbound_message_id=None,
            last_error=notes or reason,
        )
        decision = "failed"
    else:
        message.transport_status = AnalyzerTransportMessageStatus.RESEND.value
        message.ack_deadline_at = None
        _touch_transport_session(
            transport_session,
            session_status=AnalyzerTransportSessionStatus.SENDING,
        )
        decision = "resend"

    write_audit_event(
        session,
        entity_type="analyzer_transport_message",
        entity_id=message.id,
        action=f"outbound-{reason.lower()}",
        status=message.transport_status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"session_id": transport_session.id, "notes": notes},
    )
    session.commit()
    session.refresh(transport_session)
    session.refresh(message)
    return AnalyzerTransportAckResponse(
        decision=decision,
        message=_to_message_summary(message),
        session=_to_session_summary(transport_session),
    )


def _active_or_next_outbound_message(
    session: Session,
    transport_session: AnalyzerTransportSessionRecord,
) -> AnalyzerTransportMessageRecord | None:
    if transport_session.outbound_message_id:
        message = session.get(
            AnalyzerTransportMessageRecord,
            transport_session.outbound_message_id,
        )
        if message is not None:
            return message

    message = session.scalar(
        select(AnalyzerTransportMessageRecord)
        .where(
            AnalyzerTransportMessageRecord.session_id == transport_session.id,
            AnalyzerTransportMessageRecord.direction == AnalyzerTransportDirection.OUTBOUND.value,
            AnalyzerTransportMessageRecord.transport_status.in_(
                [
                    AnalyzerTransportMessageStatus.QUEUED.value,
                    AnalyzerTransportMessageStatus.READY.value,
                    AnalyzerTransportMessageStatus.RESEND.value,
                    AnalyzerTransportMessageStatus.AWAITING_ACK.value,
                ]
            ),
        )
        .order_by(AnalyzerTransportMessageRecord.created_at.asc())
        .limit(1)
    )
    if message is not None:
        _touch_transport_session(
            transport_session,
            session_status=AnalyzerTransportSessionStatus.SENDING,
            outbound_message_id=message.id,
        )
    return message


def _build_current_transport_item(
    message: AnalyzerTransportMessageRecord,
) -> AnalyzerTransportItem:
    if message.last_sent_kind == AnalyzerTransportLastSentKind.ENQ.value:
        return AnalyzerTransportItem(
            kind="control",
            control_code="ENQ",
            payload=ENQ,
            payload_escaped=escape_transport_text(ENQ),
            retry_count=message.retry_count,
        )
    if message.last_sent_kind == AnalyzerTransportLastSentKind.EOT.value:
        return AnalyzerTransportItem(
            kind="control",
            control_code="EOT",
            payload=EOT,
            payload_escaped=escape_transport_text(EOT),
            retry_count=message.retry_count,
        )
    if message.last_sent_kind == AnalyzerTransportLastSentKind.FRAME.value:
        if message.pending_frame_index is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Pending frame index is missing for FRAME resend.",
            )
        frame = (message.frames_payload or [])[message.pending_frame_index]
        return AnalyzerTransportItem(
            kind="frame",
            frame_no=int(frame["frame_no"]),
            payload=str(frame["framed_payload"]),
            payload_escaped=str(frame["framed_payload_escaped"]),
            is_final=bool(frame["is_final"]),
            checksum_hex=str(frame["checksum_hex"]),
            retry_count=message.retry_count,
        )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Message does not have a current transport item.",
    )


def _log_resend(
    session: Session,
    transport_session: AnalyzerTransportSessionRecord,
    message: AnalyzerTransportMessageRecord,
    transport_item: AnalyzerTransportItem,
) -> None:
    if transport_item.kind == "control":
        _log_frame(
            session,
            session_id=transport_session.id,
            message_id=message.id,
            direction=AnalyzerTransportDirection.OUTBOUND,
            event_kind=AnalyzerTransportEventKind.CONTROL,
            control_code=transport_item.control_code,
            framed_payload=transport_item.payload,
            retry_no=message.retry_count,
            notes="resend",
        )
        return

    frame = (message.frames_payload or [])[message.pending_frame_index or 0]
    _log_frame(
        session,
        session_id=transport_session.id,
        message_id=message.id,
        direction=AnalyzerTransportDirection.OUTBOUND,
        event_kind=AnalyzerTransportEventKind.FRAME,
        frame_no=int(frame["frame_no"]),
        payload_chunk=str(frame["payload_chunk"]),
        framed_payload=str(frame["framed_payload"]),
        checksum_hex=str(frame["checksum_hex"]),
        is_final=bool(frame["is_final"]),
        retry_no=message.retry_count,
        notes="resend",
    )


def _log_frame(
    session: Session,
    *,
    session_id: str,
    message_id: str | None,
    direction: AnalyzerTransportDirection,
    event_kind: AnalyzerTransportEventKind,
    control_code: str | None = None,
    frame_no: int | None = None,
    payload_chunk: str | None = None,
    framed_payload: str | None = None,
    checksum_hex: str | None = None,
    is_final: bool | None = None,
    accepted: bool = True,
    duplicate_flag: bool = False,
    retry_no: int = 0,
    notes: str | None = None,
) -> None:
    session.add(
        AnalyzerTransportFrameLogRecord(
            id=str(uuid4()),
            session_id=session_id,
            message_id=message_id,
            direction=direction.value,
            event_kind=event_kind.value,
            control_code=control_code,
            frame_no=frame_no,
            payload_chunk=payload_chunk,
            framed_payload=framed_payload,
            checksum_hex=checksum_hex,
            is_final=is_final,
            accepted=accepted,
            duplicate_flag=duplicate_flag,
            retry_no=retry_no,
            notes=notes,
        )
    )


def _ack_deadline(profile: AnalyzerTransportProfileRecord) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=profile.ack_timeout_seconds)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _touch_transport_session(
    transport_session: AnalyzerTransportSessionRecord,
    *,
    session_status: AnalyzerTransportSessionStatus | None = None,
    outbound_message_id: str | None | object = ...,
    inbound_message_id: str | None | object = ...,
    expected_inbound_frame_no: int | None = None,
    last_error: str | None | object = ...,
    closed_at: datetime | None | object = ...,
) -> None:
    if session_status is not None:
        transport_session.session_status = session_status.value
    if outbound_message_id is not ...:
        transport_session.outbound_message_id = outbound_message_id
    if inbound_message_id is not ...:
        transport_session.inbound_message_id = inbound_message_id
    if expected_inbound_frame_no is not None:
        transport_session.expected_inbound_frame_no = expected_inbound_frame_no
    if last_error is not ...:
        transport_session.last_error = last_error
    if closed_at is not ...:
        transport_session.closed_at = closed_at
    transport_session.last_activity_at = datetime.now(UTC)


def _ensure_transport_profile(
    session: Session,
    *,
    profile_id: UUID | None,
    device_id: UUID,
) -> AnalyzerTransportProfileRecord:
    if profile_id is not None:
        profile = session.get(AnalyzerTransportProfileRecord, str(profile_id))
        if profile is not None and profile.device_id == str(device_id) and profile.active:
            return profile
    profile = session.scalar(
        select(AnalyzerTransportProfileRecord)
        .where(
            AnalyzerTransportProfileRecord.device_id == str(device_id),
            AnalyzerTransportProfileRecord.active.is_(True),
        )
        .order_by(AnalyzerTransportProfileRecord.created_at.desc())
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active transport profile not found for device {device_id}.",
        )
    return profile


def _validate_transport_profile_payload(
    payload: AnalyzerTransportProfileCreateRequest,
) -> None:
    if payload.connection_mode == AnalyzerTransportConnectionMode.TCP_CLIENT:
        if not payload.tcp_host or payload.tcp_port is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="tcp_host and tcp_port are required for tcp-client profiles.",
            )
    if payload.connection_mode == AnalyzerTransportConnectionMode.SERIAL:
        if not payload.serial_port:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="serial_port is required for serial profiles.",
            )
    if payload.frame_payload_size < 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="frame_payload_size must be at least 10.",
        )
    if payload.ack_timeout_seconds < 0 or payload.max_retries < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ack_timeout_seconds and max_retries must be non-negative.",
        )
    if payload.poll_interval_seconds < 0 or payload.read_timeout_seconds < 0 or payload.write_timeout_seconds < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="poll/read/write timeout values must be non-negative.",
        )


def _derive_session_status(
    transport_session: AnalyzerTransportSessionRecord,
    *,
    outbound_message_id: str | None,
    inbound_message_id: str | None,
) -> AnalyzerTransportSessionStatus:
    if transport_session.closed_at is not None:
        return AnalyzerTransportSessionStatus.CLOSED
    if inbound_message_id is not None:
        return AnalyzerTransportSessionStatus.RECEIVING
    if outbound_message_id is not None:
        return AnalyzerTransportSessionStatus.SENDING
    return AnalyzerTransportSessionStatus.IDLE


def _merge_transport_error(existing: str | None, extra: str | None) -> str | None:
    if existing and extra:
        return f"{existing}; {extra}"
    return extra or existing


def _get_device_or_404(session: Session, device_id: UUID) -> DeviceRecord:
    device = session.get(DeviceRecord, str(device_id))
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} was not found.",
        )
    return device


def _get_transport_session_or_404(
    session: Session,
    session_id: UUID,
) -> AnalyzerTransportSessionRecord:
    transport_session = session.get(AnalyzerTransportSessionRecord, str(session_id))
    if transport_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transport session {session_id} was not found.",
        )
    return transport_session


def _get_transport_message_or_404(
    session: Session,
    message_id: UUID,
) -> AnalyzerTransportMessageRecord:
    message = session.get(AnalyzerTransportMessageRecord, str(message_id))
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transport message {message_id} was not found.",
        )
    return message


def _to_profile_summary(
    profile: AnalyzerTransportProfileRecord,
) -> AnalyzerTransportProfileSummary:
    return AnalyzerTransportProfileSummary(
        id=profile.id,
        device_id=profile.device_id,
        protocol=profile.protocol,
        framing_mode=profile.framing_mode,
        connection_mode=profile.connection_mode,
        tcp_host=profile.tcp_host,
        tcp_port=profile.tcp_port,
        serial_port=profile.serial_port,
        serial_baudrate=profile.serial_baudrate,
        frame_payload_size=profile.frame_payload_size,
        ack_timeout_seconds=profile.ack_timeout_seconds,
        max_retries=profile.max_retries,
        poll_interval_seconds=profile.poll_interval_seconds,
        read_timeout_seconds=profile.read_timeout_seconds,
        write_timeout_seconds=profile.write_timeout_seconds,
        auto_dispatch_astm=profile.auto_dispatch_astm,
        auto_verify=profile.auto_verify,
        active=profile.active,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _to_session_summary(
    transport_session: AnalyzerTransportSessionRecord,
) -> AnalyzerTransportSessionSummary:
    return AnalyzerTransportSessionSummary(
        id=transport_session.id,
        device_id=transport_session.device_id,
        profile_id=transport_session.profile_id,
        session_status=transport_session.session_status,
        outbound_message_id=transport_session.outbound_message_id,
        inbound_message_id=transport_session.inbound_message_id,
        expected_inbound_frame_no=transport_session.expected_inbound_frame_no,
        lease_owner=transport_session.lease_owner,
        lease_acquired_at=transport_session.lease_acquired_at,
        lease_expires_at=transport_session.lease_expires_at,
        heartbeat_at=transport_session.heartbeat_at,
        failure_count=transport_session.failure_count,
        next_retry_at=transport_session.next_retry_at,
        last_error=transport_session.last_error,
        last_activity_at=transport_session.last_activity_at,
        created_at=transport_session.created_at,
        updated_at=transport_session.updated_at,
        closed_at=transport_session.closed_at,
    )


def _to_message_summary(
    message: AnalyzerTransportMessageRecord,
) -> AnalyzerTransportMessageSummary:
    return AnalyzerTransportMessageSummary(
        id=message.id,
        session_id=message.session_id,
        device_id=message.device_id,
        direction=message.direction,
        protocol=message.protocol,
        message_type=message.message_type,
        transport_status=message.transport_status,
        logical_payload=message.logical_payload,
        assembled_payload=message.assembled_payload,
        frames=[_to_frame_payload(frame) for frame in message.frames_payload or []],
        total_frames=message.total_frames,
        next_frame_index=message.next_frame_index,
        pending_frame_index=message.pending_frame_index,
        last_sent_kind=message.last_sent_kind,
        retry_count=message.retry_count,
        correlation_key=message.correlation_key,
        ack_deadline_at=message.ack_deadline_at,
        parse_error=message.parse_error,
        dispatched_entity_type=message.dispatched_entity_type,
        dispatched_entity_id=message.dispatched_entity_id,
        created_at=message.created_at,
        updated_at=message.updated_at,
        completed_at=message.completed_at,
    )


def _to_frame_payload(frame: dict[str, str | int | bool]) -> AnalyzerTransportFramePayload:
    return AnalyzerTransportFramePayload(
        frame_no=int(frame["frame_no"]),
        payload_chunk=str(frame["payload_chunk"]),
        is_final=bool(frame["is_final"]),
        checksum_hex=str(frame["checksum_hex"]),
        framed_payload=str(frame["framed_payload"]),
        framed_payload_escaped=str(frame["framed_payload_escaped"]),
    )


def _to_frame_log_summary(
    frame_log: AnalyzerTransportFrameLogRecord,
) -> AnalyzerTransportFrameLogSummary:
    return AnalyzerTransportFrameLogSummary(
        id=frame_log.id,
        session_id=frame_log.session_id,
        message_id=frame_log.message_id,
        direction=frame_log.direction,
        event_kind=frame_log.event_kind,
        control_code=frame_log.control_code,
        frame_no=frame_log.frame_no,
        payload_chunk=frame_log.payload_chunk,
        framed_payload=frame_log.framed_payload,
        checksum_hex=frame_log.checksum_hex,
        is_final=frame_log.is_final,
        accepted=frame_log.accepted,
        duplicate_flag=frame_log.duplicate_flag,
        retry_no=frame_log.retry_no,
        notes=frame_log.notes,
        created_at=frame_log.created_at,
    )
