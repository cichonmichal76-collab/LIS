from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.integrations import (
    ASTMImportResponse,
    ASTMMessageImportRequest,
    DeviceGatewayIngestRequest,
    DeviceGatewayIngestResponse,
    DeviceWorklistResponse,
    HL7MessageImportRequest,
    HL7OrderImportResponse,
    HL7ResultImportResponse,
    InterfaceMessageSummary,
    MessageDirection,
    RawInstrumentMessageSummary,
)
from app.services import integrations as integration_service

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


@router.get("/messages", response_model=dict[str, list[InterfaceMessageSummary]])
def list_interface_messages(
    session: DbSession,
    protocol: str | None = Query(default=None),
    direction: MessageDirection | None = Query(default=None),
    message_type: str | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict[str, list[InterfaceMessageSummary]]:
    return {
        "items": integration_service.list_interface_messages(
            session,
            protocol=protocol,
            direction=direction,
            message_type=message_type,
        )
    }


@router.get("/device-gateway/messages", response_model=dict[str, list[RawInstrumentMessageSummary]])
def list_device_messages(
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
) -> dict[str, list[RawInstrumentMessageSummary]]:
    return {"items": integration_service.list_device_messages(session, device_id=device_id)}


@router.post(
    "/hl7v2/import/oml-o33",
    response_model=HL7OrderImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_oml_o33(
    payload: HL7MessageImportRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> HL7OrderImportResponse:
    return integration_service.import_hl7_oml_o33(
        session,
        payload,
        actor_user_id=str(current_user.id),
    )


@router.post(
    "/hl7v2/import/oru-r01",
    response_model=HL7ResultImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_oru_r01(
    payload: HL7MessageImportRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> HL7ResultImportResponse:
    return integration_service.import_hl7_oru_r01(
        session,
        payload,
        actor_user_id=str(current_user.id),
    )


@router.get("/hl7v2/export/oml-o33/{order_id}")
def export_oml_o33(
    order_id: UUID,
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
) -> Response:
    message = integration_service.export_hl7_oml_o33(
        session,
        order_id,
        actor_user_id=str(current_user.id),
    )
    return Response(content=message.encode("utf-8"), media_type="text/plain")


@router.get("/hl7v2/export/oru-r01/{report_id}")
def export_oru_r01(
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
) -> Response:
    message = integration_service.export_hl7_oru_r01(
        session,
        report_id,
        actor_user_id=str(current_user.id),
    )
    return Response(content=message.encode("utf-8"), media_type="text/plain")


@router.get("/astm/export/worklist/{device_id}")
def export_astm_worklist(
    device_id: UUID,
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
) -> Response:
    message = integration_service.export_astm_worklist(
        session,
        device_id,
        actor_user_id=str(current_user.id),
    )
    return Response(content=message.encode("utf-8"), media_type="text/plain")


@router.post(
    "/astm/import/results",
    response_model=ASTMImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_astm_results(
    payload: ASTMMessageImportRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> ASTMImportResponse:
    return integration_service.import_astm_results(
        session,
        payload,
        actor_user_id=str(current_user.id),
    )


@router.get("/device-gateway/worklists/{device_id}", response_model=DeviceWorklistResponse)
def get_device_worklist(
    device_id: UUID,
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
) -> DeviceWorklistResponse:
    return integration_service.get_device_worklist(session, device_id)


@router.post(
    "/device-gateway/ingest",
    response_model=DeviceGatewayIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_device_results(
    payload: DeviceGatewayIngestRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> DeviceGatewayIngestResponse:
    return integration_service.ingest_device_results(
        session,
        payload,
        actor_user_id=str(current_user.id),
    )
