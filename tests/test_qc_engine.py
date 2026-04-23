from __future__ import annotations

from datetime import UTC, datetime

from tests.support import bootstrap_admin, create_catalog_item, create_order, create_patient, make_client


def _accepted_specimen(client, headers: dict[str, str], *, order_id: str, patient_id: str, barcode: str) -> dict[str, object]:
    specimen_response = client.post(
        "/api/v1/specimens/accession",
        headers=headers,
        json={
            "order_id": order_id,
            "patient_id": patient_id,
            "specimen_type_code": "serum",
        },
    )
    assert specimen_response.status_code == 201, specimen_response.text
    specimen = specimen_response.json()
    specimen_id = specimen["id"]
    assert client.post(
        f"/api/v1/specimens/{specimen_id}/collect",
        headers=headers,
        json={"collected_at": datetime.now(UTC).isoformat(), "container_barcodes": [barcode]},
    ).status_code == 200
    assert client.post(
        f"/api/v1/specimens/{specimen_id}/receive",
        headers=headers,
        json={"received_at": datetime.now(UTC).isoformat()},
    ).status_code == 200
    assert client.post(f"/api/v1/specimens/{specimen_id}/accept", headers=headers).status_code == 200
    return specimen


def _create_qc_material_lot(client, headers: dict[str, str], *, catalog_id: str) -> tuple[dict[str, object], dict[str, object]]:
    material_response = client.post(
        "/api/v1/qc/materials",
        headers=headers,
        json={"code": "QC-GLU", "name": "Chemistry serum level 1", "manufacturer": "OpenLIS Controls"},
    )
    assert material_response.status_code == 201, material_response.text
    material = material_response.json()

    lot_response = client.post(
        "/api/v1/qc/lots",
        headers=headers,
        json={
            "material_id": material["id"],
            "lot_no": "LOT-QC-001",
            "test_catalog_id": catalog_id,
            "unit_ucum": "mg/dL",
            "target_mean": 100.0,
            "target_sd": 1.0,
            "min_value": 95.0,
            "max_value": 105.0,
        },
    )
    assert lot_response.status_code == 201, lot_response.text
    return material, lot_response.json()


def test_qc_run_evaluation_supports_warning_and_failure(tmp_path):
    with make_client(tmp_path, "lis-qc-rules.sqlite3") as client:
        headers, _ = bootstrap_admin(client)
        catalog = create_catalog_item(client, headers)
        _, lot = _create_qc_material_lot(client, headers, catalog_id=catalog["id"])

        rule_response = client.post(
            "/api/v1/qc/rules",
            headers=headers,
            json={
                "name": "Westgard 1_2s",
                "test_catalog_id": catalog["id"],
                "rule_type": "westgard_12s",
            },
        )
        assert rule_response.status_code == 201, rule_response.text
        rule_response = client.post(
            "/api/v1/qc/rules",
            headers=headers,
            json={
                "name": "Westgard 2_2s",
                "test_catalog_id": catalog["id"],
                "rule_type": "westgard_22s",
            },
        )
        assert rule_response.status_code == 201, rule_response.text

        run1_response = client.post(
            "/api/v1/qc/runs",
            headers=headers,
            json={"lot_id": lot["id"]},
        )
        assert run1_response.status_code == 201, run1_response.text
        run1 = run1_response.json()
        result1_response = client.post(
            f"/api/v1/qc/runs/{run1['id']}/results",
            headers=headers,
            json={"test_catalog_id": catalog["id"], "value_num": 102.4, "unit_ucum": "mg/dL"},
        )
        assert result1_response.status_code == 201, result1_response.text
        evaluated1 = client.post(f"/api/v1/qc/runs/{run1['id']}/evaluate", headers=headers)
        assert evaluated1.status_code == 200, evaluated1.text
        assert evaluated1.json()["run"]["status"] == "warning"
        assert evaluated1.json()["results"][0]["decision"] == "warning"
        assert "Westgard 1_2s" in evaluated1.json()["results"][0]["warning_rules"]

        run2_response = client.post(
            "/api/v1/qc/runs",
            headers=headers,
            json={"lot_id": lot["id"]},
        )
        assert run2_response.status_code == 201, run2_response.text
        run2 = run2_response.json()
        result2_response = client.post(
            f"/api/v1/qc/runs/{run2['id']}/results",
            headers=headers,
            json={"test_catalog_id": catalog["id"], "value_num": 102.6, "unit_ucum": "mg/dL"},
        )
        assert result2_response.status_code == 201, result2_response.text
        evaluated2 = client.post(f"/api/v1/qc/runs/{run2['id']}/evaluate", headers=headers)
        assert evaluated2.status_code == 200, evaluated2.text
        assert evaluated2.json()["run"]["status"] == "failed"
        assert evaluated2.json()["results"][0]["decision"] == "fail"
        assert "Westgard 2_2s" in evaluated2.json()["results"][0]["failure_rules"]


def test_qc_run_evaluation_supports_r4s_and_41s(tmp_path):
    with make_client(tmp_path, "lis-qc-westgard-advanced.sqlite3") as client:
        headers, _ = bootstrap_admin(client)
        catalog = create_catalog_item(client, headers)
        _, lot = _create_qc_material_lot(client, headers, catalog_id=catalog["id"])

        for rule_name, rule_type in [
            ("Westgard R_4s", "westgard_r4s"),
            ("Westgard 4_1s", "westgard_41s"),
        ]:
            rule_response = client.post(
                "/api/v1/qc/rules",
                headers=headers,
                json={
                    "name": rule_name,
                    "test_catalog_id": catalog["id"],
                    "rule_type": rule_type,
                },
            )
            assert rule_response.status_code == 201, rule_response.text

        for value in [101.2, 101.3, 101.4]:
            run_response = client.post("/api/v1/qc/runs", headers=headers, json={"lot_id": lot["id"]})
            assert run_response.status_code == 201, run_response.text
            run_id = run_response.json()["id"]
            result_response = client.post(
                f"/api/v1/qc/runs/{run_id}/results",
                headers=headers,
                json={"test_catalog_id": catalog["id"], "value_num": value, "unit_ucum": "mg/dL"},
            )
            assert result_response.status_code == 201, result_response.text
            evaluate_response = client.post(f"/api/v1/qc/runs/{run_id}/evaluate", headers=headers)
            assert evaluate_response.status_code == 200, evaluate_response.text
            assert evaluate_response.json()["run"]["status"] == "passed"

        run_41s_response = client.post("/api/v1/qc/runs", headers=headers, json={"lot_id": lot["id"]})
        assert run_41s_response.status_code == 201, run_41s_response.text
        run_41s_id = run_41s_response.json()["id"]
        result_41s_response = client.post(
            f"/api/v1/qc/runs/{run_41s_id}/results",
            headers=headers,
            json={"test_catalog_id": catalog["id"], "value_num": 101.6, "unit_ucum": "mg/dL"},
        )
        assert result_41s_response.status_code == 201, result_41s_response.text
        evaluated_41s = client.post(f"/api/v1/qc/runs/{run_41s_id}/evaluate", headers=headers)
        assert evaluated_41s.status_code == 200, evaluated_41s.text
        assert evaluated_41s.json()["run"]["status"] == "failed"
        assert "Westgard 4_1s" in evaluated_41s.json()["results"][0]["failure_rules"]

        run_high_response = client.post("/api/v1/qc/runs", headers=headers, json={"lot_id": lot["id"]})
        assert run_high_response.status_code == 201, run_high_response.text
        run_high_id = run_high_response.json()["id"]
        assert client.post(
            f"/api/v1/qc/runs/{run_high_id}/results",
            headers=headers,
            json={"test_catalog_id": catalog["id"], "value_num": 102.4, "unit_ucum": "mg/dL"},
        ).status_code == 201
        evaluated_high = client.post(f"/api/v1/qc/runs/{run_high_id}/evaluate", headers=headers)
        assert evaluated_high.status_code == 200, evaluated_high.text

        run_low_response = client.post("/api/v1/qc/runs", headers=headers, json={"lot_id": lot["id"]})
        assert run_low_response.status_code == 201, run_low_response.text
        run_low_id = run_low_response.json()["id"]
        assert client.post(
            f"/api/v1/qc/runs/{run_low_id}/results",
            headers=headers,
            json={"test_catalog_id": catalog["id"], "value_num": 97.7, "unit_ucum": "mg/dL"},
        ).status_code == 201
        evaluated_low = client.post(f"/api/v1/qc/runs/{run_low_id}/evaluate", headers=headers)
        assert evaluated_low.status_code == 200, evaluated_low.text
        assert evaluated_low.json()["run"]["status"] == "failed"
        assert "Westgard R_4s" in evaluated_low.json()["results"][0]["failure_rules"]


def test_qc_gate_blocks_autoverification_until_qc_passes(tmp_path):
    with make_client(tmp_path, "lis-qc-autoverification.sqlite3") as client:
        headers, _ = bootstrap_admin(client)
        patient = create_patient(client, headers)
        catalog = create_catalog_item(client, headers)
        _, lot = _create_qc_material_lot(client, headers, catalog_id=catalog["id"])

        rule_response = client.post(
            "/api/v1/autoverification/rules",
            headers=headers,
            json={
                "name": "Glucose basic rule",
                "test_catalog_id": catalog["id"],
                "specimen_type_code": "serum",
                "condition": {
                    "specimen_status_in": ["accepted"],
                    "unit_ucum_equals": "mg/dL",
                    "numeric_min": 70,
                    "numeric_max": 140,
                },
            },
        )
        assert rule_response.status_code == 201, rule_response.text

        order = create_order(client, headers, patient_id=patient["id"], catalog_id=catalog["id"])
        order_item_id = client.get(f"/api/v1/orders/{order['id']}", headers=headers).json()["items"][0]["id"]
        specimen = _accepted_specimen(
            client,
            headers,
            order_id=order["id"],
            patient_id=patient["id"],
            barcode="QC-AUTO-001",
        )

        observation_response = client.post(
            "/api/v1/observations/manual",
            headers=headers,
            json={
                "order_item_id": order_item_id,
                "specimen_id": specimen["id"],
                "code_local": catalog["local_code"],
                "status": "preliminary",
                "value_type": "quantity",
                "value_num": 101.0,
                "unit_ucum": "mg/dL",
            },
        )
        assert observation_response.status_code == 201, observation_response.text
        observation_id = observation_response.json()["id"]

        gate_response = client.get(f"/api/v1/qc/observations/{observation_id}/gate", headers=headers)
        assert gate_response.status_code == 200, gate_response.text
        assert gate_response.json()["applies"] is True
        assert gate_response.json()["allowed"] is False

        evaluation = client.post(
            f"/api/v1/autoverification/observations/{observation_id}/evaluate",
            headers=headers,
        )
        assert evaluation.status_code == 200, evaluation.text
        assert evaluation.json()["overall_decision"] == "fail"
        assert any("no evaluated QC run" in reason for reason in evaluation.json()["implicit_reasons"])

        applied = client.post(
            f"/api/v1/autoverification/observations/{observation_id}/apply",
            headers=headers,
        )
        assert applied.status_code == 200, applied.text
        assert applied.json()["decision"] == "held"
        assert any("no evaluated QC run" in reason for reason in applied.json()["reasons"])

        run_response = client.post("/api/v1/qc/runs", headers=headers, json={"lot_id": lot["id"]})
        assert run_response.status_code == 201, run_response.text
        run_id = run_response.json()["id"]
        result_response = client.post(
            f"/api/v1/qc/runs/{run_id}/results",
            headers=headers,
            json={"test_catalog_id": catalog["id"], "value_num": 100.5, "unit_ucum": "mg/dL"},
        )
        assert result_response.status_code == 201, result_response.text
        evaluated_run = client.post(f"/api/v1/qc/runs/{run_id}/evaluate", headers=headers)
        assert evaluated_run.status_code == 200, evaluated_run.text
        assert evaluated_run.json()["run"]["status"] == "passed"

        gate_after = client.get(f"/api/v1/qc/observations/{observation_id}/gate", headers=headers)
        assert gate_after.status_code == 200, gate_after.text
        assert gate_after.json()["allowed"] is True


def test_qc_gate_blocks_report_authorization_until_passing_qc_exists(tmp_path):
    with make_client(tmp_path, "lis-qc-report.sqlite3") as client:
        headers, user = bootstrap_admin(client)
        patient = create_patient(client, headers)
        catalog = create_catalog_item(client, headers)
        _, lot = _create_qc_material_lot(client, headers, catalog_id=catalog["id"])

        order = create_order(client, headers, patient_id=patient["id"], catalog_id=catalog["id"])
        order_item_id = client.get(f"/api/v1/orders/{order['id']}", headers=headers).json()["items"][0]["id"]
        specimen = _accepted_specimen(
            client,
            headers,
            order_id=order["id"],
            patient_id=patient["id"],
            barcode="QC-REP-001",
        )

        observation_response = client.post(
            "/api/v1/observations/manual",
            headers=headers,
            json={
                "order_item_id": order_item_id,
                "specimen_id": specimen["id"],
                "code_local": catalog["local_code"],
                "status": "preliminary",
                "value_type": "quantity",
                "value_num": 99.2,
                "unit_ucum": "mg/dL",
            },
        )
        assert observation_response.status_code == 201, observation_response.text
        observation_id = observation_response.json()["id"]

        technical_verify = client.post(
            f"/api/v1/observations/{observation_id}/technical-verify",
            headers=headers,
            json={"notes": "manual release pending QC gate"},
        )
        assert technical_verify.status_code == 200, technical_verify.text

        report_response = client.post(
            "/api/v1/reports/generate",
            headers=headers,
            json={"order_id": order["id"], "conclusion_text": "QC gated report"},
        )
        assert report_response.status_code == 201, report_response.text
        report_id = report_response.json()["id"]

        blocked_authorize = client.post(
            f"/api/v1/reports/{report_id}/authorize",
            headers=headers,
            json={"signed_by_user_id": user["id"]},
        )
        assert blocked_authorize.status_code == 409, blocked_authorize.text
        assert "QC gate blocks report authorization" in blocked_authorize.json()["detail"]

        run_response = client.post("/api/v1/qc/runs", headers=headers, json={"lot_id": lot["id"]})
        assert run_response.status_code == 201, run_response.text
        run_id = run_response.json()["id"]
        result_response = client.post(
            f"/api/v1/qc/runs/{run_id}/results",
            headers=headers,
            json={"test_catalog_id": catalog["id"], "value_num": 100.1, "unit_ucum": "mg/dL"},
        )
        assert result_response.status_code == 201, result_response.text
        evaluated_run = client.post(f"/api/v1/qc/runs/{run_id}/evaluate", headers=headers)
        assert evaluated_run.status_code == 200, evaluated_run.text
        assert evaluated_run.json()["run"]["status"] == "passed"

        authorize_response = client.post(
            f"/api/v1/reports/{report_id}/authorize",
            headers=headers,
            json={"signed_by_user_id": user["id"]},
        )
        assert authorize_response.status_code == 200, authorize_response.text
        assert authorize_response.json()["status"] == "final"
