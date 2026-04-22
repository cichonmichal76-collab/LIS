from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]
AUTO_SMOKE_DB = ROOT / "data" / "smoke_test_autoverification.sqlite3"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    AUTO_SMOKE_DB.parent.mkdir(parents=True, exist_ok=True)
    if AUTO_SMOKE_DB.exists():
        AUTO_SMOKE_DB.unlink()

    os.environ["LIS_DATABASE_URL"] = f"sqlite:///{AUTO_SMOKE_DB.as_posix()}"
    app = create_app()

    with TestClient(app) as client:
        bootstrap = client.post(
            "/api/v1/auth/bootstrap-admin",
            json={
                "username": "admin",
                "password": "admin12345",
                "display_name": "Admin User",
            },
        )
        assert bootstrap.status_code == 201, bootstrap.text
        auth_headers = _headers(bootstrap.json()["access_token"])

        patient = client.post(
            "/api/v1/patients",
            headers=auth_headers,
            json={
                "mrn": "MRN-AUTO-SMOKE-001",
                "given_name": "Anna",
                "family_name": "Nowak",
                "sex_code": "F",
                "birth_date": "1990-01-01",
            },
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["id"]

        catalog = client.post(
            "/api/v1/test-catalog",
            headers=auth_headers,
            json={
                "local_code": "GLU-AUTO-SMOKE",
                "display_name": "Glucose autoverify smoke",
                "kind": "orderable",
                "loinc_num": "2345-7",
                "specimen_type_code": "SER",
                "default_ucum": "mg/dL",
                "result_value_type": "quantity",
            },
        )
        assert catalog.status_code == 201, catalog.text
        catalog_id = catalog.json()["id"]

        rule = client.post(
            "/api/v1/autoverification/rules",
            headers=auth_headers,
            json={
                "name": "Smoke glucose autoverify",
                "test_catalog_id": catalog_id,
                "specimen_type_code": "SER",
                "condition": {
                    "specimen_status_in": ["accepted", "in_process"],
                    "unit_ucum_equals": "mg/dL",
                    "numeric_min": 70,
                    "numeric_max": 140,
                },
            },
        )
        assert rule.status_code == 201, rule.text

        order = client.post(
            "/api/v1/orders",
            headers=auth_headers,
            json={
                "patient_id": patient_id,
                "source_system": "smoke-auto",
                "priority": "routine",
                "ordered_at": "2026-04-22T12:00:00Z",
                "items": [{"test_catalog_id": catalog_id}],
            },
        )
        assert order.status_code == 201, order.text
        order_id = order.json()["id"]
        order_item_id = client.get(f"/api/v1/orders/{order_id}", headers=auth_headers).json()["items"][0]["id"]

        specimen = client.post(
            "/api/v1/specimens/accession",
            headers=auth_headers,
            json={
                "order_id": order_id,
                "patient_id": patient_id,
                "specimen_type_code": "SER",
            },
        )
        assert specimen.status_code == 201, specimen.text
        specimen_id = specimen.json()["id"]

        assert client.post(
            f"/api/v1/specimens/{specimen_id}/collect",
            headers=auth_headers,
            json={"collected_at": "2026-04-22T12:05:00Z", "container_barcodes": ["TUBE-AUTO-SMOKE-001"]},
        ).status_code == 200
        assert client.post(
            f"/api/v1/specimens/{specimen_id}/receive",
            headers=auth_headers,
            json={"received_at": "2026-04-22T12:10:00Z"},
        ).status_code == 200
        assert client.post(f"/api/v1/specimens/{specimen_id}/accept", headers=auth_headers).status_code == 200

        observation = client.post(
            "/api/v1/observations/manual",
            headers=auth_headers,
            json={
                "order_item_id": order_item_id,
                "specimen_id": specimen_id,
                "code_local": "GLU-AUTO-SMOKE",
                "code_loinc": "2345-7",
                "value_type": "quantity",
                "value_num": 102.4,
                "unit_ucum": "mg/dL",
                "abnormal_flag": "N",
            },
        )
        assert observation.status_code == 201, observation.text
        observation_id = observation.json()["id"]

        evaluated = client.post(
            f"/api/v1/autoverification/observations/{observation_id}/evaluate",
            headers=auth_headers,
        )
        assert evaluated.status_code == 200, evaluated.text
        assert evaluated.json()["overall_decision"] == "pass"

        applied = client.post(
            f"/api/v1/autoverification/observations/{observation_id}/apply",
            headers=auth_headers,
        )
        assert applied.status_code == 200, applied.text
        assert applied.json()["decision"] == "auto_finalized"

        observation_read = client.get(f"/api/v1/observations/{observation_id}", headers=auth_headers)
        assert observation_read.status_code == 200, observation_read.text
        assert observation_read.json()["status"] == "final"

        print("Autoverification smoke test OK")
        print(
            {
                "patient_id": patient_id,
                "order_id": order_id,
                "observation_id": observation_id,
                "rule_id": rule.json()["id"],
            }
        )


if __name__ == "__main__":
    main()
