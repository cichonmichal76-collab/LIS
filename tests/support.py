from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import hash_password
from app.db.models import UserRecord
from app.db.runtime import create_temporary_database, ensure_runtime_schema
from app.main import create_app


@contextmanager
def make_client(tmp_path, db_name: str):
    base_database_url = os.getenv("LIS_TEST_DATABASE_URL")
    cleanup = None
    if base_database_url:
        database_url, cleanup = create_temporary_database(base_database_url, db_name)
        settings = Settings(database_url=database_url, auto_create_schema=False)
    else:
        db_path = tmp_path / db_name
        database_url = f"sqlite:///{db_path.as_posix()}"
        settings = Settings(database_url=database_url, auto_create_schema=False)

    ensure_runtime_schema(settings.database_url)
    app = create_app(settings)

    try:
        with TestClient(app) as client:
            yield client
    finally:
        if cleanup is not None:
            cleanup()


def bootstrap_admin(client: TestClient) -> tuple[dict[str, str], dict[str, object]]:
    response = client.post(
        "/api/v1/auth/bootstrap-admin",
        json={
            "username": "admin",
            "password": "admin12345",
            "display_name": "Admin User",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    return {"Authorization": f"Bearer {payload['access_token']}"}, payload["user"]


def create_user(
    client: TestClient,
    *,
    username: str,
    password: str,
    display_name: str,
    role_code: str,
) -> dict[str, object]:
    session = client.app.state.db.session_factory()
    try:
        user = UserRecord(
            id=str(uuid4()),
            username=username,
            password_hash=hash_password(password),
            display_name=display_name,
            role_code=role_code,
            active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role_code": user.role_code,
        }
    finally:
        session.close()


def login(client: TestClient, *, username: str, password: str) -> tuple[dict[str, str], dict[str, object]]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    return {"Authorization": f"Bearer {payload['access_token']}"}, payload["user"]


def create_patient(client: TestClient, headers: dict[str, str]) -> dict[str, object]:
    response = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "mrn": f"MRN-{uuid4().hex[:8].upper()}",
            "given_name": "Anna",
            "family_name": "Nowak",
            "sex_code": "F",
            "birth_date": "1990-01-01",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_catalog_item(client: TestClient, headers: dict[str, str]) -> dict[str, object]:
    response = client.post(
        "/api/v1/test-catalog",
        headers=headers,
        json={
            "local_code": f"TEST-{uuid4().hex[:8].upper()}",
            "display_name": "Glucose",
            "kind": "orderable",
            "loinc_num": "2345-7",
            "specimen_type_code": "serum",
            "default_ucum": "mg/dL",
            "result_value_type": "quantity",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_order(
    client: TestClient,
    headers: dict[str, str],
    *,
    patient_id: str,
    catalog_id: str,
    priority: str = "routine",
) -> dict[str, object]:
    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "patient_id": patient_id,
            "source_system": "portal",
            "priority": priority,
            "ordered_at": datetime.now(UTC).isoformat(),
            "items": [{"test_catalog_id": catalog_id}],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
