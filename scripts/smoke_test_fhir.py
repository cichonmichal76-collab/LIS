from __future__ import annotations

import os

from _smoke_support import make_smoke_client


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    os.environ.pop("LIS_DATABASE_URL", None)

    with make_smoke_client("smoke_test_fhir") as client:
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
                "mrn": "MRN-FHIR-001",
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
                "local_code": "GLU-FHIR",
                "display_name": "Glucose FHIR",
                "kind": "orderable",
                "loinc_num": "2345-7",
                "specimen_type_code": "serum",
                "default_ucum": "mg/dL",
                "result_value_type": "quantity",
            },
        )
        assert catalog.status_code == 201, catalog.text

        order = client.post(
            "/api/v1/orders",
            headers=auth_headers,
            json={
                "patient_id": patient_id,
                "source_system": "smoke-fhir",
                "priority": "routine",
                "ordered_at": "2026-04-22T12:00:00Z",
                "items": [{"test_catalog_id": catalog.json()["id"]}],
            },
        )
        assert order.status_code == 201, order.text
        order_id = order.json()["id"]
        order_detail = client.get(f"/api/v1/orders/{order_id}", headers=auth_headers).json()
        order_item_id = order_detail["items"][0]["id"]

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
                "code_local": "GLU-FHIR",
                "code_loinc": "2345-7",
                "value_type": "quantity",
                "value_num": 101.2,
                "unit_ucum": "mg/dL",
                "reference_interval_snapshot": {"low": 70, "high": 99},
            },
        )
        assert observation.status_code == 201, observation.text
        observation_id = observation.json()["id"]
        assert client.post(
            f"/api/v1/observations/{observation_id}/technical-verify",
            headers=auth_headers,
            json={"notes": "QC passed"},
        ).status_code == 200

        report = client.post(
            "/api/v1/reports/generate",
            headers=auth_headers,
            json={
                "order_id": order_id,
                "code_local": "LAB-REPORT",
                "conclusion_text": "Glucose above target",
            },
        )
        assert report.status_code == 201, report.text
        report_id = report.json()["id"]
        assert client.post(
            f"/api/v1/reports/{report_id}/authorize",
            headers=auth_headers,
            json={"signed_by_user_id": current_user["id"]},
        ).status_code == 200

        metadata = client.get("/fhir/R4/metadata")
        assert metadata.status_code == 200, metadata.text
        assert metadata.json()["resourceType"] == "CapabilityStatement"

        patient_bundle = client.get("/fhir/R4/Patient", headers=auth_headers, params={"identifier": "MRN-FHIR-001"})
        assert patient_bundle.status_code == 200, patient_bundle.text
        assert patient_bundle.json()["total"] == 1
        assert patient_bundle.json()["entry"][0]["search"]["mode"] == "match"

        patient_read = client.get(f"/fhir/R4/Patient/{patient_id}", headers=auth_headers)
        assert patient_read.status_code == 200, patient_read.text
        assert patient_read.json()["resourceType"] == "Patient"

        service_request_bundle = client.get(
            "/fhir/R4/ServiceRequest",
            headers=auth_headers,
            params={"requisition": order.json()["requisition_no"]},
        )
        assert service_request_bundle.status_code == 200, service_request_bundle.text
        assert service_request_bundle.json()["total"] == 1

        specimen_bundle = client.get(
            "/fhir/R4/Specimen",
            headers=auth_headers,
            params={"accession": specimen.json()["accession_no"]},
        )
        assert specimen_bundle.status_code == 200, specimen_bundle.text
        assert specimen_bundle.json()["total"] == 1

        task_bundle = client.get(
            "/fhir/R4/Task",
            headers=auth_headers,
            params={"patient": f"Patient/{patient_id}", "code": "chemistry"},
        )
        assert task_bundle.status_code == 200, task_bundle.text
        assert task_bundle.json()["total"] == 1

        observation_bundle = client.get(
            "/fhir/R4/Observation",
            headers=auth_headers,
            params={"patient": f"Patient/{patient_id}", "status": "final"},
        )
        assert observation_bundle.status_code == 200, observation_bundle.text
        assert observation_bundle.json()["total"] == 1

        report_read = client.get(
            "/fhir/R4/DiagnosticReport",
            headers=auth_headers,
            params={"based-on": f"ServiceRequest/{order_item_id}"},
        )
        assert report_read.status_code == 200, report_read.text
        assert report_read.json()["entry"][0]["resource"]["resourceType"] == "DiagnosticReport"

        audit_bundle = client.get(
            "/fhir/R4/AuditEvent",
            headers=auth_headers,
            params={"entity": f"DiagnosticReport/{report_id}"},
        )
        assert audit_bundle.status_code == 200, audit_bundle.text
        assert audit_bundle.json()["total"] >= 2

        provenance_bundle = client.get(
            "/fhir/R4/Provenance",
            headers=auth_headers,
            params={"target": f"DiagnosticReport/{report_id}"},
        )
        assert provenance_bundle.status_code == 200, provenance_bundle.text
        assert provenance_bundle.json()["total"] >= 2

        print("FHIR smoke test OK")
        print(
            {
                "patient_id": patient_id,
                "order_item_id": order_item_id,
                "specimen_id": specimen_id,
                "task_id": task_id,
                "observation_id": observation_id,
                "report_id": report_id,
            }
        )


if __name__ == "__main__":
    main()
