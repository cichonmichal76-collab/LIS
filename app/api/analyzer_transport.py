from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, require_roles
from app.schemas.analyzer_transport import (
    AnalyzerTransportAckResponse,
    AnalyzerTransportDebugSnapshot,
    AnalyzerTransportDispatchASTMRequest,
    AnalyzerTransportDispatchResponse,
    AnalyzerTransportInboundControlResponse,
    AnalyzerTransportInboundFrameResponse,
    AnalyzerTransportListFramesResponse,
    AnalyzerTransportListMessagesResponse,
    AnalyzerTransportListProfilesResponse,
    AnalyzerTransportListSessionsResponse,
    AnalyzerTransportMessageSummary,
    AnalyzerTransportNextOutboundResponse,
    AnalyzerTransportProfileCreateRequest,
    AnalyzerTransportProfileSummary,
    AnalyzerTransportQueueOutboundRequest,
    AnalyzerTransportReceiveControlRequest,
    AnalyzerTransportReceiveFrameRequest,
    AnalyzerTransportSessionCreateRequest,
    AnalyzerTransportSessionSummary,
)
from app.schemas.auth import RoleCode, UserSummary
from app.services import analyzer_transport as transport_service

router = APIRouter(prefix="/api/v1/analyzer-transport", tags=["analyzer-transport"])


@router.post("/profiles", response_model=AnalyzerTransportProfileSummary, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: AnalyzerTransportProfileCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN)),
) -> AnalyzerTransportProfileSummary:
    return transport_service.create_profile(session, payload, actor=current_user)


@router.get("/profiles", response_model=AnalyzerTransportListProfilesResponse)
def list_profiles(
    session: DbSession,
    device_id: UUID | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> AnalyzerTransportListProfilesResponse:
    return transport_service.list_profiles(session, device_id=device_id)


@router.post("/sessions", response_model=AnalyzerTransportSessionSummary, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: AnalyzerTransportSessionCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> AnalyzerTransportSessionSummary:
    return transport_service.create_session(session, payload, actor=current_user)


@router.get("/sessions", response_model=AnalyzerTransportListSessionsResponse)
def list_sessions(
    session: DbSession,
    device_id: UUID | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> AnalyzerTransportListSessionsResponse:
    return transport_service.list_sessions(session, device_id=device_id)


@router.get("/sessions/{session_id}", response_model=AnalyzerTransportSessionSummary)
def get_session(
    session_id: UUID,
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
) -> AnalyzerTransportSessionSummary:
    return transport_service.get_session(session, session_id)


@router.get("/sessions/{session_id}/messages", response_model=AnalyzerTransportListMessagesResponse)
def list_messages(
    session_id: UUID,
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
) -> AnalyzerTransportListMessagesResponse:
    return transport_service.list_messages(session, session_id=session_id)


@router.get("/sessions/{session_id}/frames", response_model=AnalyzerTransportListFramesResponse)
def list_frames(
    session_id: UUID,
    session: DbSession,
    message_id: UUID | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> AnalyzerTransportListFramesResponse:
    return transport_service.list_frames(session, session_id=session_id, message_id=message_id)


@router.post(
    "/sessions/{session_id}/queue-outbound",
    response_model=AnalyzerTransportMessageSummary,
    status_code=status.HTTP_201_CREATED,
)
def queue_outbound(
    session_id: UUID,
    payload: AnalyzerTransportQueueOutboundRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> AnalyzerTransportMessageSummary:
    return transport_service.queue_outbound_message(
        session,
        session_id=session_id,
        payload=payload,
        actor=current_user,
    )


@router.post(
    "/sessions/{session_id}/queue-astm-worklist",
    response_model=AnalyzerTransportDebugSnapshot,
    status_code=status.HTTP_201_CREATED,
)
def queue_astm_worklist(
    session_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> AnalyzerTransportDebugSnapshot:
    return transport_service.queue_astm_worklist(session, session_id=session_id, actor=current_user)


@router.post("/sessions/{session_id}/outbound/next", response_model=AnalyzerTransportNextOutboundResponse)
def next_outbound(
    session_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> AnalyzerTransportNextOutboundResponse:
    return transport_service.next_outbound_transport_item(session, session_id=session_id)


@router.post("/sessions/{session_id}/outbound/ack", response_model=AnalyzerTransportAckResponse)
def acknowledge_outbound(
    session_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> AnalyzerTransportAckResponse:
    return transport_service.acknowledge_outbound(
        session,
        session_id=session_id,
        positive=True,
        actor=current_user,
        notes="manual-ack-endpoint",
    )


@router.post("/sessions/{session_id}/outbound/nak", response_model=AnalyzerTransportAckResponse)
def negative_ack_outbound(
    session_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> AnalyzerTransportAckResponse:
    return transport_service.acknowledge_outbound(
        session,
        session_id=session_id,
        positive=False,
        actor=current_user,
        notes="manual-nak-endpoint",
    )


@router.post("/sessions/{session_id}/outbound/timeout", response_model=AnalyzerTransportAckResponse)
def timeout_outbound(
    session_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> AnalyzerTransportAckResponse:
    return transport_service.timeout_outbound(
        session,
        session_id=session_id,
        actor=current_user,
        notes="manual-timeout-endpoint",
    )


@router.post(
    "/sessions/{session_id}/inbound/control",
    response_model=AnalyzerTransportInboundControlResponse,
)
def receive_inbound_control(
    session_id: UUID,
    payload: AnalyzerTransportReceiveControlRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> AnalyzerTransportInboundControlResponse:
    return transport_service.receive_transport_control(
        session,
        session_id=session_id,
        payload=payload,
        actor=current_user,
    )


@router.post("/sessions/{session_id}/inbound/frame", response_model=AnalyzerTransportInboundFrameResponse)
def receive_inbound_frame(
    session_id: UUID,
    payload: AnalyzerTransportReceiveFrameRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> AnalyzerTransportInboundFrameResponse:
    return transport_service.receive_transport_frame(
        session,
        session_id=session_id,
        payload=payload,
        actor=current_user,
    )


@router.post(
    "/messages/{message_id}/dispatch/astm",
    response_model=AnalyzerTransportDispatchResponse,
)
def dispatch_astm(
    message_id: UUID,
    payload: AnalyzerTransportDispatchASTMRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> AnalyzerTransportDispatchResponse:
    return transport_service.dispatch_astm_message(
        session,
        message_id=message_id,
        payload=payload,
        actor=current_user,
    )
