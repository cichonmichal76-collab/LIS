from __future__ import annotations

from datetime import UTC, datetime

from tests.support import bootstrap_admin, create_order, create_patient, make_client


def test_device_gateway_worklist_and_ingest_flow(tmp_path):
    with make_client(tmp_path, "lis-device-gateway.sqlite3") as client:
        headers, _ = bootstrap_admin(client)
        patient = create_patient(client, headers)

        catalog_response = client.post(
            "/api/v1/test-catalog",
            headers=headers,
            json={
                "local_code": "GLU-DEVICE",
                "display_name": "Glucose device",
                "kind": "orderable",
                "loinc_num": "2345-7",
                "specimen_type_code": "serum",
                "default_ucum": "mg/dL",
                "result_value_type": "quantity",
            },
        )
        assert catalog_response.status_code == 201, catalog_response.text
        catalog = catalog_response.json()

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
        assert specimen_response.status_code == 201, specimen_response.text
        specimen = specimen_response.json()
        specimen_id = specimen["id"]

        assert client.post(
            f"/api/v1/specimens/{specimen_id}/collect",
            headers=headers,
            json={
                "collected_at": datetime.now(UTC).isoformat(),
                "container_barcodes": ["TUBE-DEVICE-001"],
            },
        ).status_code == 200
        assert client.post(
            f"/api/v1/specimens/{specimen_id}/receive",
            headers=headers,
            json={"received_at": datetime.now(UTC).isoformat()},
        ).status_code == 200
        assert client.post(f"/api/v1/specimens/{specimen_id}/accept", headers=headers).status_code == 200

        device_response = client.post(
            "/api/v1/devices",
            headers=headers,
            json={
                "code": "CHEM-01",
                "display_name": "Chemistry Analyzer 01",
                "protocol": "device-gateway",
                "manufacturer": "Acme",
                "model": "CX-1",
            },
        )
        assert device_response.status_code == 201, device_response.text
        device = device_response.json()

        mapping_response = client.post(
            f"/api/v1/devices/{device['id']}/mappings",
            headers=headers,
            json={
                "incoming_test_code": "GLU-AN",
                "test_catalog_id": catalog["id"],
                "default_unit_ucum": "mg/dL",
            },
        )
        assert mapping_response.status_code == 201, mapping_response.text

        task_response = client.post(
            "/api/v1/tasks",
            headers=headers,
            json={
                "focus_type": "order-item",
                "focus_id": order_item_id,
                "based_on_order_item_id": order_item_id,
                "queue_code": "chemistry-device",
                "status": "ready",
                "device_id": device["id"],
            },
        )
        assert task_response.status_code == 201, task_response.text

        worklist_response = client.get(
            f"/api/v1/integrations/device-gateway/worklists/{device['id']}",
            headers=headers,
        )
        assert worklist_response.status_code == 200, worklist_response.text
        worklist = worklist_response.json()
        assert len(worklist["items"]) == 1
        assert worklist["items"][0]["specimen_barcode"] == "TUBE-DEVICE-001"
        assert worklist["items"][0]["incoming_test_code"] == "GLU-AN"

        ingest_response = client.post(
            "/api/v1/integrations/device-gateway/ingest",
            headers=headers,
            json={
                "device_id": device["id"],
                "protocol": "device-gateway",
                "specimen_barcode": "TUBE-DEVICE-001",
                "auto_verify": True,
                "results": [
                    {
                        "incoming_test_code": "GLU-AN",
                        "value_type": "quantity",
                        "value_num": 98.7,
                        "unit_ucum": "mg/dL",
                        "effective_at": datetime.now(UTC).isoformat(),
                    }
                ],
            },
        )
        assert ingest_response.status_code == 201, ingest_response.text
        ingest = ingest_response.json()
        assert ingest["errors"] == []
        assert len(ingest["created_observations"]) == 1
        created_observation = ingest["created_observations"][0]
        assert created_observation["status"] == "final"
        assert created_observation["raw_message_id"] is not None

        message_response = client.get(
            "/api/v1/integrations/device-gateway/messages",
            headers=headers,
            params={"device_id": device["id"]},
        )
        assert message_response.status_code == 200, message_response.text
        messages = message_response.json()["items"]
        assert len(messages) == 1
        assert messages[0]["created_observation_count"] == 1
        assert messages[0]["parsed_ok"] is True

        completed_tasks = client.get(
            "/api/v1/tasks",
            headers=headers,
            params={"queue": "chemistry-device", "status": "completed"},
        )
        assert completed_tasks.status_code == 200, completed_tasks.text
        assert len(completed_tasks.json()["items"]) == 1


def test_hl7_import_and_export_flow(tmp_path):
    with make_client(tmp_path, "lis-hl7.sqlite3") as client:
        headers, user = bootstrap_admin(client)

        catalog_response = client.post(
            "/api/v1/test-catalog",
            headers=headers,
            json={
                "local_code": "GLU-HL7",
                "display_name": "Glucose HL7",
                "kind": "orderable",
                "loinc_num": "2345-7",
                "specimen_type_code": "serum",
                "default_ucum": "mg/dL",
                "result_value_type": "quantity",
            },
        )
        assert catalog_response.status_code == 201, catalog_response.text

        oml_message = "\n".join(
            [
                "MSH|^~\\&|HIS|WARD|LIS|LAB|20260422120000||OML^O33|CTRL-OML-001|P|2.5.1",
                "PID|1||MRN-HL7-001^^^HIS^MR||Nowak^Anna||19900101|F",
                "ORC|NW|REQ-HL7-001|REQ-HL7-001",
                "SPM|1|ACC-HL7-001^LIS||serum^serum^L",
                "OBR|1|REQ-HL7-001|REQ-HL7-001|GLU-HL7^Glucose HL7^L",
            ]
        )
        import_oml = client.post(
            "/api/v1/integrations/hl7v2/import/oml-o33",
            headers=headers,
            json={"message": oml_message, "create_missing_patient": True},
        )
        assert import_oml.status_code == 201, import_oml.text
        imported_order = import_oml.json()
        order_id = imported_order["order"]["id"]
        order_item_id = imported_order["items"][0]["id"]
        specimen_id = imported_order["specimens"][0]["id"]
        assert imported_order["patient"]["mrn"] == "MRN-HL7-001"
        assert imported_order["order"]["requisition_no"] == "REQ-HL7-001"

        export_oml = client.get(
            f"/api/v1/integrations/hl7v2/export/oml-o33/{order_id}",
            headers=headers,
        )
        assert export_oml.status_code == 200, export_oml.text
        assert "OML^O33" in export_oml.text
        assert "REQ-HL7-001" in export_oml.text

        oru_message = "\n".join(
            [
                "MSH|^~\\&|ANALYZER|CHEM|LIS|LAB|20260422121500||ORU^R01|CTRL-ORU-001|P|2.5.1",
                "PID|1||MRN-HL7-001^^^HIS^MR||Nowak^Anna||19900101|F",
                "SPM|1|ACC-HL7-001^LIS||serum^serum^L",
                "ORC|RE|REQ-HL7-001|REQ-HL7-001",
                "OBR|1|REQ-HL7-001|REQ-HL7-001|GLU-HL7^Glucose HL7^L",
                "OBX|1|NM|GLU-HL7^Glucose HL7^L||105.4|mg/dL|70-99||||F|||20260422121500",
            ]
        )
        import_oru = client.post(
            "/api/v1/integrations/hl7v2/import/oru-r01",
            headers=headers,
            json={"message": oru_message},
        )
        assert import_oru.status_code == 201, import_oru.text
        imported_result = import_oru.json()
        assert imported_result["order_id"] == order_id
        assert imported_result["specimen_id"] == specimen_id
        assert len(imported_result["observations"]) == 1
        observation_id = imported_result["observations"][0]["id"]
        assert imported_result["observations"][0]["status"] == "final"

        report_response = client.post(
            "/api/v1/reports/generate",
            headers=headers,
            json={"order_id": order_id, "conclusion_text": "HL7 import report"},
        )
        assert report_response.status_code == 201, report_response.text
        report_id = report_response.json()["id"]

        authorize_response = client.post(
            f"/api/v1/reports/{report_id}/authorize",
            headers=headers,
            json={"signed_by_user_id": user["id"]},
        )
        assert authorize_response.status_code == 200, authorize_response.text

        export_oru = client.get(
            f"/api/v1/integrations/hl7v2/export/oru-r01/{report_id}",
            headers=headers,
        )
        assert export_oru.status_code == 200, export_oru.text
        assert "ORU^R01" in export_oru.text
        assert "OBX|" in export_oru.text
        assert report_response.json()["report_no"] in export_oru.text

        interface_messages = client.get(
            "/api/v1/integrations/messages",
            headers=headers,
            params={"protocol": "hl7v2"},
        )
        assert interface_messages.status_code == 200, interface_messages.text
        assert len(interface_messages.json()["items"]) >= 4

        fhir_report = client.get(
            "/fhir/R4/DiagnosticReport",
            headers=headers,
            params={"based-on": f"ServiceRequest/{order_item_id}"},
        )
        assert fhir_report.status_code == 200, fhir_report.text
        assert fhir_report.json()["entry"][0]["resource"]["result"][0]["reference"] == (
            f"Observation/{observation_id}"
        )
