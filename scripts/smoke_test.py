from __future__ import annotations

import os

from _smoke_support import make_smoke_client

__test__ = False


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    os.environ.pop("LIS_DATABASE_URL", None)

    with make_smoke_client("smoke_test") as client:
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
        current_user = bootstrap.json()["user"]

        patient = client.post(
            "/api/v1/patients",
            headers=auth_headers,
            json={
                "mrn": "MRN-SMOKE-001",
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
                "local_code": "GLU-SMOKE",
                "display_name": "Glucose smoke",
                "kind": "orderable",
                "loinc_num": "2345-7",
                "specimen_type_code": "serum",
                "default_ucum": "mg/dL",
                "result_value_type": "quantity",
            },
        )
        assert catalog.status_code == 201, catalog.text
        catalog_id = catalog.json()["id"]

        order = client.post(
            "/api/v1/orders",
            headers=auth_headers,
            json={
                "patient_id": patient_id,
                "source_system": "smoke",
                "priority": "routine",
                "ordered_at": "2026-04-22T12:00:00Z",
                "items": [{"test_catalog_id": catalog_id}],
            },
        )
        assert order.status_code == 201, order.text
        order_json = order.json()
        order_id = order_json["id"]
        order_item_id = client.get(f"/api/v1/orders/{order_id}", headers=auth_headers).json()["items"][0]["id"]

        specimen = client.post(
            "/api/v1/specimens/accession",
            headers=auth_headers,
            json={
                "order_id": order_id,
                "patient_id": patient_id,
                "specimen_type_code": "serum",
            },
        )
        assert specimen.status_code == 201, specimen.text
        specimen_id = specimen.json()["id"]

        assert client.post(
            f"/api/v1/specimens/{specimen_id}/collect",
            headers=auth_headers,
            json={"collected_at": "2026-04-22T12:05:00Z"},
        ).status_code == 200
        assert client.post(
            f"/api/v1/specimens/{specimen_id}/receive",
            headers=auth_headers,
            json={"received_at": "2026-04-22T12:10:00Z"},
        ).status_code == 200
        assert client.post(f"/api/v1/specimens/{specimen_id}/accept", headers=auth_headers).status_code == 200

        task = client.post(
            "/api/v1/tasks",
            headers=auth_headers,
            json={
                "focus_type": "order-item",
                "focus_id": order_item_id,
                "based_on_order_item_id": order_item_id,
                "queue_code": "chemistry",
                "status": "ready",
            },
        )
        assert task.status_code == 201, task.text
        task_id = task.json()["id"]
        assert client.post(f"/api/v1/tasks/{task_id}/start", headers=auth_headers).status_code == 200
        assert client.post(f"/api/v1/tasks/{task_id}/complete", headers=auth_headers).status_code == 200

        observation = client.post(
            "/api/v1/observations/manual",
            headers=auth_headers,
            json={
                "order_item_id": order_item_id,
                "specimen_id": specimen_id,
                "code_local": "GLU-SMOKE",
                "code_loinc": "2345-7",
                "value_type": "quantity",
                "value_num": 102.5,
                "unit_ucum": "mg/dL",
                "reference_interval_snapshot": {"low": 70, "high": 99},
            },
        )
        assert observation.status_code == 201, observation.text
        observation_id = observation.json()["id"]

        verified = client.post(
            f"/api/v1/observations/{observation_id}/technical-verify",
            headers=auth_headers,
            json={"notes": "QC passed"},
        )
        assert verified.status_code == 200, verified.text

        report = client.post(
            "/api/v1/reports/generate",
            headers=auth_headers,
            json={
                "order_id": order_id,
                "code_local": "LAB-REPORT",
                "conclusion_text": "Glucose above fasting target",
            },
        )
        assert report.status_code == 201, report.text
        report_id = report.json()["id"]

        authorized = client.post(
            f"/api/v1/reports/{report_id}/authorize",
            headers=auth_headers,
            json={"signed_by_user_id": current_user["id"]},
        )
        assert authorized.status_code == 200, authorized.text
        assert authorized.json()["status"] == "final"

        pdf_response = client.get(
            f"/api/v1/reports/{report_id}/pdf",
            headers=auth_headers,
            params={"version": 2},
        )
        assert pdf_response.status_code == 200, pdf_response.text
        assert pdf_response.headers["content-type"] == "application/pdf"

        print("Smoke test OK")
        print(
            {
                "patient_id": patient_id,
                "order_id": order_id,
                "specimen_id": specimen_id,
                "observation_id": observation_id,
                "report_id": report_id,
            }
        )


if __name__ == "__main__":
    main()
