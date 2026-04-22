from __future__ import annotations

from datetime import UTC, datetime

from tests.support import bootstrap_admin, create_catalog_item, create_order, create_patient, make_client


def test_observation_report_authorization_flow(tmp_path):
    with make_client(tmp_path, "lis-observation-report.sqlite3") as client:
        headers, user = bootstrap_admin(client)
        patient = create_patient(client, headers)
        catalog = create_catalog_item(client, headers)
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
                "specimen_type_code": "serum",
            },
        )
        assert specimen_response.status_code == 201
        specimen_id = specimen_response.json()["id"]
        client.post(
            f"/api/v1/specimens/{specimen_id}/collect",
            headers=headers,
            json={"collected_at": datetime.now(UTC).isoformat()},
        )
        client.post(
            f"/api/v1/specimens/{specimen_id}/receive",
            headers=headers,
            json={"received_at": datetime.now(UTC).isoformat()},
        )
        client.post(f"/api/v1/specimens/{specimen_id}/accept", headers=headers)

        observation_response = client.post(
            "/api/v1/observations/manual",
            headers=headers,
            json={
                "order_item_id": order_item_id,
                "specimen_id": specimen_id,
                "code_local": catalog["local_code"],
                "status": "preliminary",
                "value_type": "quantity",
                "value_num": 97.4,
                "unit_ucum": "mg/dL",
                "reference_interval_snapshot": {"low": 70, "high": 99},
            },
        )
        assert observation_response.status_code == 201
        observation_id = observation_response.json()["id"]
        assert observation_response.json()["status"] == "preliminary"

        technical_verify_response = client.post(
            f"/api/v1/observations/{observation_id}/technical-verify",
            headers=headers,
            json={"notes": "QC passed"},
        )
        assert technical_verify_response.status_code == 200
        assert technical_verify_response.json()["status"] == "final"

        list_observations_response = client.get(
            "/api/v1/observations",
            headers=headers,
            params={"order_item_id": order_item_id},
        )
        assert list_observations_response.status_code == 200
        assert len(list_observations_response.json()["items"]) == 1

        report_response = client.post(
            "/api/v1/reports/generate",
            headers=headers,
            json={"order_id": order["id"], "conclusion_text": "Preliminary chemistry report"},
        )
        assert report_response.status_code == 201
        report = report_response.json()
        report_id = report["id"]
        assert report["status"] == "preliminary"
        assert report["current_version_no"] == 1
        assert report["observation_ids"] == [observation_id]

        authorize_response = client.post(
            f"/api/v1/reports/{report_id}/authorize",
            headers=headers,
            json={"signed_by_user_id": user["id"]},
        )
        assert authorize_response.status_code == 200
        assert authorize_response.json()["status"] == "final"
        assert authorize_response.json()["current_version_no"] == 2

        pdf_response = client.get(
            f"/api/v1/reports/{report_id}/pdf",
            headers=headers,
            params={"version": 2},
        )
        assert pdf_response.status_code == 200
        assert pdf_response.headers["content-type"] == "application/pdf"
        assert "version=2" in pdf_response.text

        amend_response = client.post(
            f"/api/v1/reports/{report_id}/amend",
            headers=headers,
            json={
                "signed_by_user_id": user["id"],
                "reason": "Clarified interpretation",
                "conclusion_text": "Final report with clarified interpretation",
            },
        )
        assert amend_response.status_code == 200
        assert amend_response.json()["status"] == "amended"
        assert amend_response.json()["current_version_no"] == 3
        assert len(amend_response.json()["versions"]) == 3

        audit_response = client.get(
            "/api/v1/audit",
            headers=headers,
            params={"entity_type": "diagnostic_report", "entity_id": report_id},
        )
        assert audit_response.status_code == 200
        assert len(audit_response.json()["items"]) == 3

        provenance_response = client.get(
            "/api/v1/provenance",
            headers=headers,
            params={"target_resource_type": "diagnostic_report", "target_resource_id": report_id},
        )
        assert provenance_response.status_code == 200
        assert len(provenance_response.json()["items"]) == 3


def test_observation_correction_creates_replacement(tmp_path):
    with make_client(tmp_path, "lis-observation-correct.sqlite3") as client:
        headers, _ = bootstrap_admin(client)
        patient = create_patient(client, headers)
        catalog = create_catalog_item(client, headers)
        order = create_order(
            client,
            headers,
            patient_id=patient["id"],
            catalog_id=catalog["id"],
        )
        order_item_id = client.get(f"/api/v1/orders/{order['id']}", headers=headers).json()["items"][0]["id"]

        create_response = client.post(
            "/api/v1/observations/manual",
            headers=headers,
            json={
                "order_item_id": order_item_id,
                "code_local": "HGB",
                "status": "preliminary",
                "value_type": "quantity",
                "value_num": 12.1,
                "unit_ucum": "g/dL",
            },
        )
        assert create_response.status_code == 201
        original_id = create_response.json()["id"]

        correct_response = client.post(
            f"/api/v1/observations/{original_id}/correct",
            headers=headers,
            json={
                "reason": "Transcription fix",
                "replacement": {
                    "order_item_id": order_item_id,
                    "code_local": "HGB",
                    "status": "preliminary",
                    "value_type": "quantity",
                    "value_num": 12.8,
                    "unit_ucum": "g/dL",
                },
            },
        )
        assert correct_response.status_code == 200
        corrected = correct_response.json()
        assert corrected["id"] != original_id
        assert corrected["value_num"] == 12.8

        observations_response = client.get(
            "/api/v1/observations",
            headers=headers,
            params={"order_item_id": order_item_id},
        )
        assert observations_response.status_code == 200
        statuses = {item["id"]: item["status"] for item in observations_response.json()["items"]}
        assert statuses[original_id] == "corrected"
        assert statuses[corrected["id"]] == "preliminary"
