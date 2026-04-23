from __future__ import annotations

import os

from _smoke_support import make_smoke_client


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    os.environ.pop("LIS_DATABASE_URL", None)

    with make_smoke_client("smoke_test_qc") as client:
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
        admin_user = bootstrap.json()["user"]

        patient = client.post(
            "/api/v1/patients",
            headers=auth_headers,
            json={
                "mrn": "MRN-QC-SMOKE-001",
                "given_name": "Jan",
                "family_name": "Kowalski",
                "sex_code": "M",
                "birth_date": "1985-05-05",
            },
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["id"]

        catalog = client.post(
            "/api/v1/test-catalog",
            headers=auth_headers,
            json={
                "local_code": "GLU-QC-SMOKE",
                "display_name": "Glucose QC smoke",
                "kind": "orderable",
                "loinc_num": "2345-7",
                "specimen_type_code": "serum",
                "default_ucum": "mg/dL",
                "result_value_type": "quantity",
            },
        )
        assert catalog.status_code == 201, catalog.text
        catalog_id = catalog.json()["id"]

        material = client.post(
            "/api/v1/qc/materials",
            headers=auth_headers,
            json={"code": "QC-SMOKE-GLU", "name": "Glucose control"},
        )
        assert material.status_code == 201, material.text
        material_id = material.json()["id"]

        lot = client.post(
            "/api/v1/qc/lots",
            headers=auth_headers,
            json={
                "material_id": material_id,
                "lot_no": "QC-SMOKE-LOT-1",
                "test_catalog_id": catalog_id,
                "unit_ucum": "mg/dL",
                "target_mean": 100.0,
                "target_sd": 1.5,
                "min_value": 95.0,
                "max_value": 105.0,
            },
        )
        assert lot.status_code == 201, lot.text
        lot_id = lot.json()["id"]

        qc_rule = client.post(
            "/api/v1/qc/rules",
            headers=auth_headers,
            json={
                "name": "QC smoke 1_2s",
                "test_catalog_id": catalog_id,
                "rule_type": "westgard_12s",
            },
        )
        assert qc_rule.status_code == 201, qc_rule.text

        qc_run = client.post("/api/v1/qc/runs", headers=auth_headers, json={"lot_id": lot_id})
        assert qc_run.status_code == 201, qc_run.text
        qc_run_id = qc_run.json()["id"]

        qc_result = client.post(
            f"/api/v1/qc/runs/{qc_run_id}/results",
            headers=auth_headers,
            json={"test_catalog_id": catalog_id, "value_num": 100.4, "unit_ucum": "mg/dL"},
        )
        assert qc_result.status_code == 201, qc_result.text

        qc_evaluate = client.post(f"/api/v1/qc/runs/{qc_run_id}/evaluate", headers=auth_headers)
        assert qc_evaluate.status_code == 200, qc_evaluate.text
        assert qc_evaluate.json()["run"]["status"] == "passed"

        auto_rule = client.post(
            "/api/v1/autoverification/rules",
            headers=auth_headers,
            json={
                "name": "QC smoke autoverify",
                "test_catalog_id": catalog_id,
                "specimen_type_code": "serum",
                "condition": {
                    "specimen_status_in": ["accepted"],
                    "unit_ucum_equals": "mg/dL",
                    "numeric_min": 70,
                    "numeric_max": 140,
                },
            },
        )
        assert auto_rule.status_code == 201, auto_rule.text

        order = client.post(
            "/api/v1/orders",
            headers=auth_headers,
            json={
                "patient_id": patient_id,
                "source_system": "smoke-qc",
                "priority": "routine",
                "ordered_at": "2026-04-23T10:00:00Z",
                "items": [{"test_catalog_id": catalog_id}],
            },
        )
        assert order.status_code == 201, order.text
        order_id = order.json()["id"]
        order_item_id = client.get(f"/api/v1/orders/{order_id}", headers=auth_headers).json()["items"][0]["id"]

        specimen = client.post(
            "/api/v1/specimens/accession",
            headers=auth_headers,
            json={"order_id": order_id, "patient_id": patient_id, "specimen_type_code": "serum"},
        )
        assert specimen.status_code == 201, specimen.text
        specimen_id = specimen.json()["id"]
        assert client.post(
            f"/api/v1/specimens/{specimen_id}/collect",
            headers=auth_headers,
            json={"collected_at": "2026-04-23T10:05:00Z", "container_barcodes": ["QC-SMOKE-TUBE-1"]},
        ).status_code == 200
        assert client.post(
            f"/api/v1/specimens/{specimen_id}/receive",
            headers=auth_headers,
            json={"received_at": "2026-04-23T10:10:00Z"},
        ).status_code == 200
        assert client.post(f"/api/v1/specimens/{specimen_id}/accept", headers=auth_headers).status_code == 200

        observation = client.post(
            "/api/v1/observations/manual",
            headers=auth_headers,
            json={
                "order_item_id": order_item_id,
                "specimen_id": specimen_id,
                "code_local": "GLU-QC-SMOKE",
                "code_loinc": "2345-7",
                "value_type": "quantity",
                "value_num": 101.1,
                "unit_ucum": "mg/dL",
                "abnormal_flag": "N",
            },
        )
        assert observation.status_code == 201, observation.text
        observation_id = observation.json()["id"]

        gate = client.get(f"/api/v1/qc/observations/{observation_id}/gate", headers=auth_headers)
        assert gate.status_code == 200, gate.text
        assert gate.json()["allowed"] is True

        applied = client.post(
            f"/api/v1/autoverification/observations/{observation_id}/apply",
            headers=auth_headers,
        )
        assert applied.status_code == 200, applied.text
        assert applied.json()["decision"] == "auto_finalized"

        report = client.post(
            "/api/v1/reports/generate",
            headers=auth_headers,
            json={"order_id": order_id, "conclusion_text": "QC smoke report"},
        )
        assert report.status_code == 201, report.text
        report_id = report.json()["id"]

        authorized = client.post(
            f"/api/v1/reports/{report_id}/authorize",
            headers=auth_headers,
            json={"signed_by_user_id": admin_user["id"]},
        )
        assert authorized.status_code == 200, authorized.text
        assert authorized.json()["status"] == "final"

        print("QC smoke test OK")
        print(
            {
                "patient_id": patient_id,
                "order_id": order_id,
                "qc_run_id": qc_run_id,
                "observation_id": observation_id,
                "report_id": report_id,
            }
        )


if __name__ == "__main__":
    main()
