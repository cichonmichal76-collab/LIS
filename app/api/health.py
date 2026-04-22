from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.core.config import APP_VERSION
from app.db.runtime import detect_database_backend
from app.schemas.common import HealthResponse

router = APIRouter(tags=["system"])
CONTRACT_FILE = Path(__file__).resolve().parents[2] / "openapi" / "lis-internal-v1.yaml"


@router.get("/health", response_model=HealthResponse, summary="Read service health")
def get_health(request: Request) -> HealthResponse:
    database_url = request.app.state.settings.database_url
    database_backend = detect_database_backend(database_url)
    try:
        with request.app.state.db.engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database ping failed: {exc}",
        ) from exc
    return HealthResponse(
        service="lis-core",
        status="ok",
        version=APP_VERSION,
        contract_path="/openapi/lis-internal-v1.yaml",
        database_backend=database_backend,
        database_status="ok",
    )


@router.get("/openapi/lis-internal-v1.yaml", include_in_schema=False)
def get_internal_contract() -> FileResponse:
    return FileResponse(CONTRACT_FILE, media_type="application/yaml", filename=CONTRACT_FILE.name)
