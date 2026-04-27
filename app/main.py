from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.analyzer_transport import router as analyzer_transport_router
from app.api.autoverification import router as autoverification_router
from app.api.dashboard import router as dashboard_router
from app.api.fhir import router as fhir_router
from app.api.health import router as health_router
from app.api.qc import router as qc_router
from app.api.catalog import router as catalog_router
from app.api.devices import router as devices_router
from app.api.integrations import router as integrations_router
from app.api.orders import router as orders_router
from app.api.patients import router as patients_router
from app.api.specimens import router as specimens_router
from app.api.tasks import router as tasks_router
from app.api.observations import router as observations_router
from app.api.reports import router as reports_router
from app.api.audit import router as audit_router
from app.core.config import APP_NAME, APP_VERSION, Settings
from app.db.session import DatabaseSessionManager

UI_DIR = Path(__file__).resolve().parent / "ui"
UI_INDEX_FILE = UI_DIR / "index.html"


def create_app(settings: Settings | None = None) -> FastAPI:
    effective_settings = settings or Settings.from_env()
    db = DatabaseSessionManager(effective_settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = effective_settings
        app.state.db = db
        if effective_settings.auto_create_schema:
            db.create_schema(mode=effective_settings.schema_bootstrap_mode)
        try:
            yield
        finally:
            db.dispose()

    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        summary="Starter modular monolith for a laboratory information system",
        description=(
            "Internal API with working persistence for auth, master data, orders, "
            "specimen lifecycle, task orchestration, observations, reports, audit, "
            "provenance, device registry, HL7 v2 integrations, device gateway, "
            "autoverification, QC engine, ASTM-style drivers, analyzer transport "
            "sessions, and a read/search FHIR facade."
        ),
        lifespan=lifespan,
    )

    app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

    app.include_router(health_router)
    app.include_router(fhir_router)
    app.include_router(auth_router)
    app.include_router(analyzer_transport_router)
    app.include_router(autoverification_router)
    app.include_router(dashboard_router)
    app.include_router(qc_router)
    app.include_router(patients_router)
    app.include_router(catalog_router)
    app.include_router(devices_router)
    app.include_router(integrations_router)
    app.include_router(orders_router)
    app.include_router(specimens_router)
    app.include_router(tasks_router)
    app.include_router(observations_router)
    app.include_router(reports_router)
    app.include_router(audit_router)

    def root_payload() -> dict[str, str]:
        return {
            "service": "lis-core",
            "status": "ok",
            "ui": "/dashboard",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "contract": "/openapi/lis-internal-v1.yaml",
            "fhir_metadata": "/fhir/R4/metadata",
            "database_url": effective_settings.database_url,
        }

    def wants_html(request: Request) -> bool:
        requested_format = request.query_params.get("format")
        if requested_format == "json":
            return False
        if requested_format == "html":
            return True

        accept = request.headers.get("accept", "*/*").lower()
        if "application/json" in accept and "text/html" not in accept:
            return False
        return "text/html" in accept

    @app.get("/dashboard", include_in_schema=False)
    def read_dashboard() -> FileResponse:
        return FileResponse(UI_INDEX_FILE)

    @app.get("/", tags=["system"])
    def read_root(request: Request):
        if wants_html(request):
            return FileResponse(UI_INDEX_FILE)
        return JSONResponse(root_payload())

    return app


app = create_app()
