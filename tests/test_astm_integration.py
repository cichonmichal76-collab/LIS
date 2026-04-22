from __future__ import annotations

from datetime import UTC, datetime

from tests.support import bootstrap_admin, create_order, create_patient, make_client


def test_astm_worklist_export_and_result_import(tmp_path):
    with make_client(tmp_path, "lis-astm.sqlite3") as client:
        headers, _ = bootstrap_admin(client)
        patient = create_patient(client, headers)

        catalog_response = client.post(
            "/api/v1/test-catalog",
            headers=headers,
            json={
                "local_code": "GLU-ASTM",
                "display_name": "Glucose ASTM",
                "kind": "orderable",
                "loinc_num": "2345-7",
                "specimen_type_code": "SER",
                "default_ucum": "mg/dL",
                "result_value_type": "quantity",
            },
        )
        assert catalog_response.status_code == 201, catalog_response.text
        catalog = catalog_response.json()

        device_response = client.post(
            "/api/v1/devices",
            headers=headers,
            json={
                "code": "ASTM-01",
                "display_name": "ASTM analyzer",
                "protocol": "astm",
            },
        )
        assert device_response.status_code == 201, device_response.text
        device = device_response.json()

        mapping_response = client.post(
            f"/api/v1/devices/{device['id']}/mappings",
            headers=headers,
            json={
                "incoming_test_code": "GLU-ASTM",
                "test_catalog_id": catalog["id"],
                "default_unit_ucum": "mg/dL",
            },
        )
        assert mapping_response.status_code == 201, mapping_response.text

        rule_response = client.post(
            "/api/v1/autoverification/rules",
            headers=headers,
            json={
                "name": "ASTM glucose autoverify",
                "test_catalog_id": catalog["id"],
                "device_id": device["id"],
                "condition": {
                    "specimen_status_in": ["accepted", "in_process"],
                    "unit_ucum_equals": "mg/dL",
                    "numeric_min": 60,
                    "numeric_max": 150,
                },
            },
        )
        assert rule_response.status_code == 201, rule_response.text

        order = create_order(
            client,
            headers,
            patient_id=patient["id"],
            catalog_id=catalog["id"],
        )
        order_detail = client.get(f"/api/v1/orders/{order['id']}", headers=headers).json()
        order_item_id = order_detail["items"][0]["id"]

        specimen_response = client.post(
            "/api/v1/specimens/accession",
            headers=headers,
            json={
                "order_id": order["id"],
                "patient_id": patient["id"],
                "specimen_type_code": "SER",
                "notes": "ASTM specimen",
            },
        )
        assert specimen_response.status_code == 201, specimen_response.text
        specimen = specimen_response.json()
        specimen_id = specimen["id"]
        accession_no = specimen["accession_no"]

        assert client.post(
            f"/api/v1/specimens/{specimen_id}/collect",
            headers=headers,
            json={"collected_at": datetime.now(UTC).isoformat(), "container_barcodes": ["TUBE-ASTM-001"]},
        ).status_code == 200
        assert client.post(
            f"/api/v1/specimens/{specimen_id}/receive",
            headers=headers,
            json={"received_at": datetime.now(UTC).isoformat()},
        ).status_code == 200
        assert client.post(f"/api/v1/specimens/{specimen_id}/accept", headers=headers).status_code == 200

        worklist = client.get(
            f"/api/v1/integrations/astm/export/worklist/{device['id']}",
            headers=headers,
        )
        assert worklist.status_code == 200, worklist.text
        assert accession_no in worklist.text
        assert "GLU-ASTM" in worklist.text

        message = "\r".join(
            [
                r"H|\^&|||ASTM-01|||||P|1",
                f"P|1||{patient['mrn']}||{patient['family_name']}^{patient['given_name']}",
                f"O|1|{accession_no}||GLU-ASTM^Glucose ASTM|R",
                "R|1|GLU-ASTM^Glucose ASTM|99.4|mg/dL|N||F|20260422112900",
                "L|1|N",
                "",
            ]
        )
        imported = client.post(
            "/api/v1/integrations/astm/import/results",
            headers=headers,
            json={
                "device_id": device["id"],
                "message": message,
                "auto_verify": True,
            },
        )
        assert imported.status_code == 201, imported.text
        imported_json = imported.json()
        assert len(imported_json["created_observations"]) == 1
        observation = imported_json["created_observations"][0]
        assert observation["status"] == "final"
        assert observation["autoverification"]["decision"] == "auto_finalized"
        assert observation["order_item_id"] == order_item_id
