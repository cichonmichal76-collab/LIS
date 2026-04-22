from __future__ import annotations

from datetime import UTC, datetime

from tests.support import bootstrap_admin, create_catalog_item, create_order, create_patient, make_client


def test_fhir_capability_statement_lists_supported_resources(tmp_path):
    with make_client(tmp_path, "lis-fhir-metadata.sqlite3") as client:
        response = client.get("/fhir/R4/metadata")
        assert response.status_code == 200
        payload = response.json()
        assert payload["resourceType"] == "CapabilityStatement"
        resource_types = [resource["type"] for resource in payload["rest"][0]["resource"]]
        assert "Patient" in resource_types
        assert "DiagnosticReport" in resource_types
        assert "Provenance" in resource_types


def test_fhir_read_and_search_flow(tmp_path):
    with make_client(tmp_path, "lis-fhir-flow.sqlite3") as client:
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

        specimen = client.post(
            "/api/v1/specimens/accession",
            headers=headers,
            json={
                "order_id": order["id"],
                "patient_id": patient["id"],
                "specimen_type_code": "serum",
            },
        )
        assert specimen.status_code == 201
        specimen_id = specimen.json()["id"]
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

        task = client.post(
            "/api/v1/tasks",
            headers=headers,
            json={
                "focus_type": "order-item",
                "focus_id": order_item_id,
                "based_on_order_item_id": order_item_id,
                "queue_code": "chemistry",
                "status": "ready",
            },
        )
        assert task.status_code == 201
        task_id = task.json()["id"]
        client.post(f"/api/v1/tasks/{task_id}/start", headers=headers)
        client.post(f"/api/v1/tasks/{task_id}/complete", headers=headers)

        observation = client.post(
            "/api/v1/observations/manual",
            headers=headers,
            json={
                "order_item_id": order_item_id,
                "specimen_id": specimen_id,
                "code_local": catalog["local_code"],
                "code_loinc": catalog["loinc_num"],
                "value_type": "quantity",
                "value_num": 101.8,
                "unit_ucum": "mg/dL",
            },
        )
        assert observation.status_code == 201
        observation_id = observation.json()["id"]
        client.post(
            f"/api/v1/observations/{observation_id}/technical-verify",
            headers=headers,
            json={"notes": "QC passed"},
        )

        report = client.post(
            "/api/v1/reports/generate",
            headers=headers,
            json={"order_id": order["id"], "conclusion_text": "FHIR facade report"},
        )
        assert report.status_code == 201
        report_id = report.json()["id"]
        client.post(
            f"/api/v1/reports/{report_id}/authorize",
            headers=headers,
            json={"signed_by_user_id": user["id"]},
        )

        patient_bundle = client.get(
            "/fhir/R4/Patient",
            headers=headers,
            params={"identifier": patient["mrn"]},
        )
        assert patient_bundle.status_code == 200
        assert patient_bundle.json()["total"] == 1
        assert patient_bundle.json()["entry"][0]["search"]["mode"] == "match"

        service_request_bundle = client.get(
            "/fhir/R4/ServiceRequest",
            headers=headers,
            params={"requisition": order["requisition_no"]},
        )
        assert service_request_bundle.status_code == 200
        service_request_resource = service_request_bundle.json()["entry"][0]["resource"]
        assert service_request_resource["resourceType"] == "ServiceRequest"
        assert service_request_resource["requisition"]["value"] == order["requisition_no"]

        specimen_bundle = client.get(
            "/fhir/R4/Specimen",
            headers=headers,
            params={"accession": specimen.json()["accession_no"]},
        )
        assert specimen_bundle.status_code == 200
        specimen_resource = specimen_bundle.json()["entry"][0]["resource"]
        assert specimen_resource["accessionIdentifier"]["value"] == specimen.json()["accession_no"]
        assert specimen_resource["request"][0]["reference"] == f"ServiceRequest/{order_item_id}"

        task_bundle = client.get(
            "/fhir/R4/Task",
            headers=headers,
            params={"patient": f"Patient/{patient['id']}", "code": "chemistry"},
        )
        assert task_bundle.status_code == 200
        task_resource = task_bundle.json()["entry"][0]["resource"]
        assert task_resource["id"] == task_id
        assert task_resource["for"]["reference"] == f"Patient/{patient['id']}"
        assert task_resource["code"]["coding"][0]["code"] == "chemistry"

        observation_read = client.get(f"/fhir/R4/Observation/{observation_id}", headers=headers)
        assert observation_read.status_code == 200
        assert observation_read.json()["status"] == "final"

        report_search = client.get(
            "/fhir/R4/DiagnosticReport",
            headers=headers,
            params={"based-on": f"ServiceRequest/{order_item_id}"},
        )
        assert report_search.status_code == 200
        report_resource = report_search.json()["entry"][0]["resource"]
        assert report_resource["result"][0]["reference"] == f"Observation/{observation_id}"
        assert report_resource["basedOn"][0]["reference"] == f"ServiceRequest/{order_item_id}"
        assert report_resource["presentedForm"][0]["contentType"] == "application/pdf"

        audit_bundle = client.get(
            "/fhir/R4/AuditEvent",
            headers=headers,
            params={"entity": f"DiagnosticReport/{report_id}"},
        )
        assert audit_bundle.status_code == 200
        assert audit_bundle.json()["total"] >= 2

        provenance_bundle = client.get(
            "/fhir/R4/Provenance",
            headers=headers,
            params={"target": f"DiagnosticReport/{report_id}"},
        )
        assert provenance_bundle.status_code == 200
        assert provenance_bundle.json()["total"] >= 2
