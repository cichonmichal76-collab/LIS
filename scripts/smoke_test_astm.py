from __future__ import annotations

import os

from _smoke_support import make_smoke_client


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    os.environ.pop("LIS_DATABASE_URL", None)

    with make_smoke_client("smoke_test_astm") as client:
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
                "mrn": "MRN-ASTM-SMOKE-001",
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
                "local_code": "GLU-ASTM-SMOKE",
                "display_name": "Glucose ASTM smoke",
                "kind": "orderable",
                "loinc_num": "2345-7",
                "specimen_type_code": "SER",
                "default_ucum": "mg/dL",
                "result_value_type": "quantity",
            },
        )
        assert catalog.status_code == 201, catalog.text
        catalog_id = catalog.json()["id"]

        device = client.post(
            "/api/v1/devices",
            headers=auth_headers,
            json={
                "code": "ASTM-SMOKE-01",
                "display_name": "ASTM smoke analyzer",
                "protocol": "astm",
            },
        )
        assert device.status_code == 201, device.text
        device_id = device.json()["id"]

        assert client.post(
            f"/api/v1/devices/{device_id}/mappings",
            headers=auth_headers,
            json={
                "incoming_test_code": "GLU-ASTM-SMOKE",
                "test_catalog_id": catalog_id,
                "default_unit_ucum": "mg/dL",
            },
        ).status_code == 201

        assert client.post(
            "/api/v1/autoverification/rules",
            headers=auth_headers,
            json={
                "name": "ASTM smoke autoverify",
                "test_catalog_id": catalog_id,
                "device_id": device_id,
                "condition": {
                    "specimen_status_in": ["accepted", "in_process"],
                    "unit_ucum_equals": "mg/dL",
                    "numeric_min": 60,
                    "numeric_max": 150,
                },
            },
        ).status_code == 201

        order = client.post(
            "/api/v1/orders",
            headers=auth_headers,
            json={
                "patient_id": patient_id,
                "source_system": "smoke-astm",
                "priority": "routine",
                "ordered_at": "2026-04-22T12:00:00Z",
                "items": [{"test_catalog_id": catalog_id}],
            },
        )
        assert order.status_code == 201, order.text
        order_id = order.json()["id"]

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
        accession_no = specimen.json()["accession_no"]
        specimen_id = specimen.json()["id"]

        assert client.post(
            f"/api/v1/specimens/{specimen_id}/collect",
            headers=auth_headers,
            json={"collected_at": "2026-04-22T12:05:00Z", "container_barcodes": ["TUBE-ASTM-SMOKE-001"]},
        ).status_code == 200
        assert client.post(
            f"/api/v1/specimens/{specimen_id}/receive",
            headers=auth_headers,
            json={"received_at": "2026-04-22T12:10:00Z"},
        ).status_code == 200
        assert client.post(f"/api/v1/specimens/{specimen_id}/accept", headers=auth_headers).status_code == 200

        worklist = client.get(
            f"/api/v1/integrations/astm/export/worklist/{device_id}",
            headers=auth_headers,
        )
        assert worklist.status_code == 200, worklist.text
        assert accession_no in worklist.text

        message = "\r".join(
            [
                r"H|\^&|||ASTM-SMOKE-01|||||P|1",
                "P|1||MRN-ASTM-SMOKE-001||Nowak^Anna",
                f"O|1|{accession_no}||GLU-ASTM-SMOKE^Glucose ASTM smoke|R",
                "R|1|GLU-ASTM-SMOKE^Glucose ASTM smoke|99.4|mg/dL|N||F|20260422112900",
                "L|1|N",
                "",
            ]
        )
        imported = client.post(
            "/api/v1/integrations/astm/import/results",
            headers=auth_headers,
            json={
                "device_id": device_id,
                "message": message,
                "auto_verify": True,
            },
        )
        assert imported.status_code == 201, imported.text
        imported_json = imported.json()
        assert imported_json["created_observations"][0]["status"] == "final"
        assert imported_json["created_observations"][0]["autoverification"]["decision"] == "auto_finalized"

        print("ASTM smoke test OK")
        print(
            {
                "patient_id": patient_id,
                "order_id": order_id,
                "device_id": device_id,
                "specimen_id": specimen_id,
                "raw_message_id": imported_json["raw_message_id"],
            }
        )


if __name__ == "__main__":
    main()
