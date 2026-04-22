from __future__ import annotations

import os

from _smoke_support import make_smoke_client


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    os.environ.pop("LIS_DATABASE_URL", None)

    with make_smoke_client("smoke_test_integration") as client:
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
                "mrn": "MRN-INT-001",
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
                "local_code": "GLU-INT",
                "display_name": "Glucose integration",
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
                "source_system": "smoke-integration",
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
                "specimen_type_code": "serum",
            },
        )
        assert specimen.status_code == 201, specimen.text
        specimen_id = specimen.json()["id"]
        accession_no = specimen.json()["accession_no"]

        assert client.post(
            f"/api/v1/specimens/{specimen_id}/collect",
            headers=auth_headers,
            json={
                "collected_at": "2026-04-22T12:05:00Z",
                "container_barcodes": ["TUBE-INT-001"],
            },
        ).status_code == 200
        assert client.post(
            f"/api/v1/specimens/{specimen_id}/receive",
            headers=auth_headers,
            json={"received_at": "2026-04-22T12:10:00Z"},
        ).status_code == 200
        assert client.post(f"/api/v1/specimens/{specimen_id}/accept", headers=auth_headers).status_code == 200

        device = client.post(
            "/api/v1/devices",
            headers=auth_headers,
            json={
                "code": "CHEM-SMOKE",
                "display_name": "Chemistry Smoke Analyzer",
                "protocol": "device-gateway",
            },
        )
        assert device.status_code == 201, device.text
        device_id = device.json()["id"]

        assert client.post(
            f"/api/v1/devices/{device_id}/mappings",
            headers=auth_headers,
            json={
                "incoming_test_code": "GLU-RAW",
                "test_catalog_id": catalog_id,
                "default_unit_ucum": "mg/dL",
            },
        ).status_code == 201

        worklist = client.get(
            f"/api/v1/integrations/device-gateway/worklists/{device_id}",
            headers=auth_headers,
        )
        assert worklist.status_code == 200, worklist.text
        assert worklist.json()["items"][0]["incoming_test_code"] == "GLU-RAW"

        ingest = client.post(
            "/api/v1/integrations/device-gateway/ingest",
            headers=auth_headers,
            json={
                "device_id": device_id,
                "protocol": "device-gateway",
                "accession_no": accession_no,
                "auto_verify": True,
                "results": [
                    {
                        "incoming_test_code": "GLU-RAW",
                        "value_type": "quantity",
                        "value_num": 103.2,
                        "unit_ucum": "mg/dL",
                        "effective_at": "2026-04-22T12:12:00Z",
                    }
                ],
            },
        )
        assert ingest.status_code == 201, ingest.text
        observation_id = ingest.json()["created_observations"][0]["id"]

        report = client.post(
            "/api/v1/reports/generate",
            headers=auth_headers,
            json={"order_id": order_id, "conclusion_text": "Integration smoke report"},
        )
        assert report.status_code == 201, report.text
        report_id = report.json()["id"]
        assert client.post(
            f"/api/v1/reports/{report_id}/authorize",
            headers=auth_headers,
            json={"signed_by_user_id": current_user["id"]},
        ).status_code == 200

        hl7_oml = client.get(
            f"/api/v1/integrations/hl7v2/export/oml-o33/{order_id}",
            headers=auth_headers,
        )
        assert hl7_oml.status_code == 200, hl7_oml.text
        assert "OML^O33" in hl7_oml.text

        hl7_oru = client.get(
            f"/api/v1/integrations/hl7v2/export/oru-r01/{report_id}",
            headers=auth_headers,
        )
        assert hl7_oru.status_code == 200, hl7_oru.text
        assert "ORU^R01" in hl7_oru.text

        interface_messages = client.get(
            "/api/v1/integrations/messages",
            headers=auth_headers,
            params={"protocol": "hl7v2"},
        )
        assert interface_messages.status_code == 200, interface_messages.text
        assert interface_messages.json()["items"]

        print("Integration smoke test OK")
        print(
            {
                "patient_id": patient_id,
                "order_id": order_id,
                "order_item_id": order_item_id,
                "specimen_id": specimen_id,
                "device_id": device_id,
                "observation_id": observation_id,
                "report_id": report_id,
            }
        )


if __name__ == "__main__":
    main()
