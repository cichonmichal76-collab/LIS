from __future__ import annotations

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.orders import router as orders_router
from app.api.specimens import router as specimens_router
from app.api.tasks import router as tasks_router

app = FastAPI(
    title="LIS Core API",
    version="0.1.0",
    summary="Starter modular monolith for a laboratory information system",
    description=(
        "Internal API skeleton for LIS v1. The checked-in contract focuses on orders, "
        "specimen lifecycle, and task orchestration."
    ),
)

app.include_router(health_router)
app.include_router(orders_router)
app.include_router(specimens_router)
app.include_router(tasks_router)


@app.get("/", tags=["system"])
def read_root() -> dict[str, str]:
    return {
        "service": "lis-core",
        "status": "ok",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "contract": "/openapi/lis-internal-v1.yaml",
    }
