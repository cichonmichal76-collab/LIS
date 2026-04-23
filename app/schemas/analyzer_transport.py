from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel
from app.schemas.integrations import ASTMImportResponse


class AnalyzerTransportProtocol(str, Enum):
    ASTM_TRANSPORT = "astm-transport"


class AnalyzerTransportFramingMode(str, Enum):
    ASTM_E1381 = "astm-e1381"


class AnalyzerTransportConnectionMode(str, Enum):
    MOCK = "mock"
    TCP_CLIENT = "tcp-client"
    SERIAL = "serial"


class AnalyzerTransportSessionStatus(str, Enum):
    IDLE = "idle"
    SENDING = "sending"
    RECEIVING = "receiving"
    AWAITING_ACK = "awaiting_ack"
    CLOSED = "closed"
    ERROR = "error"


class AnalyzerTransportDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class AnalyzerTransportMessageStatus(str, Enum):
    QUEUED = "queued"
    READY = "ready"
    AWAITING_ACK = "awaiting_ack"
    RESEND = "resend"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    RECEIVING = "receiving"
    RECEIVED = "received"
    DISPATCHED = "dispatched"


class AnalyzerTransportEventKind(str, Enum):
    CONTROL = "control"
    FRAME = "frame"


class AnalyzerTransportLastSentKind(str, Enum):
    ENQ = "ENQ"
    FRAME = "FRAME"
    EOT = "EOT"


class AnalyzerTransportProfileCreateRequest(ApiModel):
    device_id: UUID
    protocol: AnalyzerTransportProtocol = AnalyzerTransportProtocol.ASTM_TRANSPORT
    framing_mode: AnalyzerTransportFramingMode = AnalyzerTransportFramingMode.ASTM_E1381
    connection_mode: AnalyzerTransportConnectionMode = AnalyzerTransportConnectionMode.MOCK
    tcp_host: str | None = None
    tcp_port: int | None = None
    serial_port: str | None = None
    serial_baudrate: int | None = None
    frame_payload_size: int = 240
    ack_timeout_seconds: int = 30
    max_retries: int = 3
    poll_interval_seconds: int = 1
    read_timeout_seconds: int = 1
    write_timeout_seconds: int = 5
    auto_dispatch_astm: bool = True
    auto_verify: bool = False
    active: bool = True


class AnalyzerTransportProfileSummary(ApiModel):
    id: UUID
    device_id: UUID
    protocol: AnalyzerTransportProtocol
    framing_mode: AnalyzerTransportFramingMode
    connection_mode: AnalyzerTransportConnectionMode
    tcp_host: str | None = None
    tcp_port: int | None = None
    serial_port: str | None = None
    serial_baudrate: int | None = None
    frame_payload_size: int
    ack_timeout_seconds: int
    max_retries: int
    poll_interval_seconds: int
    read_timeout_seconds: int
    write_timeout_seconds: int
    auto_dispatch_astm: bool
    auto_verify: bool
    active: bool
    created_at: datetime
    updated_at: datetime


class AnalyzerTransportSessionCreateRequest(ApiModel):
    device_id: UUID
    profile_id: UUID | None = None


class AnalyzerTransportSessionSummary(ApiModel):
    id: UUID
    device_id: UUID
    profile_id: UUID
    session_status: AnalyzerTransportSessionStatus
    outbound_message_id: UUID | None = None
    inbound_message_id: UUID | None = None
    expected_inbound_frame_no: int
    lease_owner: str | None = None
    lease_acquired_at: datetime | None = None
    lease_expires_at: datetime | None = None
    heartbeat_at: datetime | None = None
    failure_count: int = 0
    next_retry_at: datetime | None = None
    last_error: str | None = None
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None


class AnalyzerTransportFramePayload(ApiModel):
    frame_no: int
    payload_chunk: str
    is_final: bool
    checksum_hex: str
    framed_payload: str
    framed_payload_escaped: str


class AnalyzerTransportMessageSummary(ApiModel):
    id: UUID
    session_id: UUID
    device_id: UUID
    direction: AnalyzerTransportDirection
    protocol: str
    message_type: str
    transport_status: AnalyzerTransportMessageStatus
    logical_payload: str
    assembled_payload: str | None = None
    frames: list[AnalyzerTransportFramePayload] = Field(default_factory=list)
    total_frames: int
    next_frame_index: int
    pending_frame_index: int | None = None
    last_sent_kind: AnalyzerTransportLastSentKind | None = None
    retry_count: int
    correlation_key: str | None = None
    ack_deadline_at: datetime | None = None
    parse_error: str | None = None
    dispatched_entity_type: str | None = None
    dispatched_entity_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class AnalyzerTransportFrameLogSummary(ApiModel):
    id: UUID
    session_id: UUID
    message_id: UUID | None = None
    direction: AnalyzerTransportDirection
    event_kind: AnalyzerTransportEventKind
    control_code: str | None = None
    frame_no: int | None = None
    payload_chunk: str | None = None
    framed_payload: str | None = None
    checksum_hex: str | None = None
    is_final: bool | None = None
    accepted: bool
    duplicate_flag: bool
    retry_no: int
    notes: str | None = None
    created_at: datetime


class AnalyzerTransportQueueOutboundRequest(ApiModel):
    protocol: AnalyzerTransportProtocol = AnalyzerTransportProtocol.ASTM_TRANSPORT
    message_type: str
    logical_payload: str
    correlation_key: str | None = None


class AnalyzerTransportReceiveControlRequest(ApiModel):
    control_code: str


class AnalyzerTransportReceiveFrameRequest(ApiModel):
    framed_payload: str
    auto_dispatch_astm: bool = False
    auto_verify: bool = False


class AnalyzerTransportDispatchASTMRequest(ApiModel):
    auto_verify: bool = False


class AnalyzerTransportMessageActionRequest(ApiModel):
    notes: str | None = None


class AnalyzerTransportItem(ApiModel):
    kind: str
    control_code: str | None = None
    payload: str
    payload_escaped: str
    frame_no: int | None = None
    is_final: bool | None = None
    checksum_hex: str | None = None
    retry_count: int = 0


class AnalyzerTransportParsedFrame(ApiModel):
    frame_no: int
    payload_chunk: str
    is_final: bool
    checksum_hex: str
    expected_checksum_hex: str
    checksum_ok: bool
    framed_payload: str
    framed_payload_escaped: str


class AnalyzerTransportNextOutboundResponse(ApiModel):
    session: AnalyzerTransportSessionSummary
    message: AnalyzerTransportMessageSummary | None = None
    transport_item: AnalyzerTransportItem | None = None
    awaiting_ack: bool = False
    ack_timeout_seconds: int | None = None


class AnalyzerTransportAckResponse(ApiModel):
    decision: str
    message: AnalyzerTransportMessageSummary
    session: AnalyzerTransportSessionSummary


class AnalyzerTransportInboundControlResponse(ApiModel):
    reply_control_code: str | None = None
    reply_payload: str | None = None
    reply_payload_escaped: str | None = None
    session: AnalyzerTransportSessionSummary
    message: AnalyzerTransportMessageSummary | None = None


class AnalyzerTransportDispatchResponse(ApiModel):
    message: AnalyzerTransportMessageSummary
    dispatch: ASTMImportResponse


class AnalyzerTransportInboundFrameResponse(ApiModel):
    reply_control_code: str
    reply_payload: str
    reply_payload_escaped: str
    accepted: bool
    duplicate: bool = False
    assembled: bool = False
    error: str | None = None
    session: AnalyzerTransportSessionSummary
    message: AnalyzerTransportMessageSummary
    parsed_frame: AnalyzerTransportParsedFrame | None = None
    dispatch: ASTMImportResponse | None = None


class AnalyzerTransportMessageActionResponse(ApiModel):
    action: str
    session: AnalyzerTransportSessionSummary
    message: AnalyzerTransportMessageSummary


class AnalyzerTransportListProfilesResponse(ApiModel):
    items: list[AnalyzerTransportProfileSummary] = Field(default_factory=list)


class AnalyzerTransportListSessionsResponse(ApiModel):
    items: list[AnalyzerTransportSessionSummary] = Field(default_factory=list)


class AnalyzerTransportListMessagesResponse(ApiModel):
    items: list[AnalyzerTransportMessageSummary] = Field(default_factory=list)


class AnalyzerTransportListFramesResponse(ApiModel):
    items: list[AnalyzerTransportFrameLogSummary] = Field(default_factory=list)


class AnalyzerTransportRuntimeOverview(ApiModel):
    profile_count: int
    session_count: int
    leased_session_count: int
    stale_lease_count: int
    backoff_session_count: int
    error_session_count: int
    items: list[AnalyzerTransportSessionSummary] = Field(default_factory=list)


class AnalyzerTransportRuntimeMetrics(ApiModel):
    profile_count: int
    session_count: int
    message_count: int
    leased_session_count: int
    stale_lease_count: int
    backoff_session_count: int
    error_session_count: int
    active_outbound_session_count: int
    active_inbound_session_count: int
    queued_outbound_count: int
    ready_outbound_count: int
    awaiting_ack_count: int
    resend_count: int
    failed_message_count: int
    dead_letter_count: int
    receiving_inbound_count: int
    received_inbound_count: int
    dispatched_count: int
    completed_outbound_count: int
    status_counts: dict[str, int] = Field(default_factory=dict)


class AnalyzerTransportDebugSnapshot(ApiModel):
    session: AnalyzerTransportSessionSummary
    message: AnalyzerTransportMessageSummary | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
