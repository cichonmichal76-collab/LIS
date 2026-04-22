from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.schemas.common import HealthResponse

router = APIRouter(tags=["system"])
CONTRACT_FILE = Path(__file__).resolve().parents[2] / "openapi" / "lis-internal-v1.yaml"


@router.get("/health", response_model=HealthResponse, summary="Read service health")
def get_health() -> HealthResponse:
    return HealthResponse(
        service="lis-core",
        status="ok",
        version="0.1.0",
        contract_path="/openapi/lis-internal-v1.yaml",
    )


@router.get("/openapi/lis-internal-v1.yaml", include_in_schema=False)
def get_internal_contract() -> FileResponse:
    return FileResponse(CONTRACT_FILE, media_type="application/yaml", filename=CONTRACT_FILE.name)
