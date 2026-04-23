from __future__ import annotations

from datetime import UTC, datetime

from tests.support import bootstrap_admin, create_order, create_patient, make_client


def _accepted_specimen(client, headers: dict[str, str], *, order_id: str, patient_id: str, barcode: str):
    specimen_response = client.post(
        "/api/v1/specimens/accession",
        headers=headers,
        json={
            "order_id": order_id,
            "patient_id": patient_id,
            "specimen_type_code": "SER",
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


def test_autoverification_pass_and_hold_flow(tmp_path):
    with make_client(tmp_path, "lis-autoverification.sqlite3") as client:
        headers, _ = bootstrap_admin(client)
        patient = create_patient(client, headers)

        catalog_response = client.post(
            "/api/v1/test-catalog",
            headers=headers,
            json={
                "local_code": "GLU-AUTO",
                "display_name": "Glucose autoverify",
                "kind": "orderable",
                "loinc_num": "2345-7",
                "specimen_type_code": "SER",
                "default_ucum": "mg/dL",
                "result_value_type": "quantity",
            },
        )
        assert catalog_response.status_code == 201, catalog_response.text
        catalog = catalog_response.json()

        rule_response = client.post(
            "/api/v1/autoverification/rules",
            headers=headers,
            json={
                "name": "Basic glucose chemistry rule",
                "priority": 10,
                "test_catalog_id": catalog["id"],
                "specimen_type_code": "SER",
                "condition": {
                    "specimen_status_in": ["accepted", "in_process"],
                    "unit_ucum_equals": "mg/dL",
                    "numeric_min": 70,
                    "numeric_max": 140,
                    "disallow_abnormal_flags": ["HH", "LL", "A"],
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
        specimen = _accepted_specimen(
            client,
            headers,
            order_id=order["id"],
            patient_id=patient["id"],
            barcode="TUBE-AUTO-001",
        )
        specimen_id = specimen["id"]

        observation_ok = client.post(
            "/api/v1/observations/manual",
            headers=headers,
            json={
                "order_item_id": order_item_id,
                "specimen_id": specimen_id,
                "code_local": "GLU-AUTO",
                "code_loinc": "2345-7",
                "value_type": "quantity",
                "value_num": 111.4,
                "unit_ucum": "mg/dL",
                "abnormal_flag": "N",
            },
        )
        assert observation_ok.status_code == 201, observation_ok.text
        observation_ok_id = observation_ok.json()["id"]

        evaluated = client.post(
            f"/api/v1/autoverification/observations/{observation_ok_id}/evaluate",
            headers=headers,
        )
        assert evaluated.status_code == 200, evaluated.text
        assert evaluated.json()["overall_decision"] == "pass"
        assert evaluated.json()["matched_rule_count"] == 1

        applied = client.post(
            f"/api/v1/autoverification/observations/{observation_ok_id}/apply",
            headers=headers,
        )
        assert applied.status_code == 200, applied.text
        assert applied.json()["decision"] == "auto_finalized"

        obs_final = client.get(f"/api/v1/observations/{observation_ok_id}", headers=headers)
        assert obs_final.status_code == 200, obs_final.text
        assert obs_final.json()["status"] == "final"

        observation_bad = client.post(
            "/api/v1/observations/manual",
            headers=headers,
            json={
                "order_item_id": order_item_id,
                "specimen_id": specimen_id,
                "code_local": "GLU-AUTO",
                "code_loinc": "2345-7",
                "value_type": "quantity",
                "value_num": 260.0,
                "unit_ucum": "mg/dL",
                "abnormal_flag": "H",
            },
        )
        assert observation_bad.status_code == 201, observation_bad.text
        observation_bad_id = observation_bad.json()["id"]

        applied_bad = client.post(
            f"/api/v1/autoverification/observations/{observation_bad_id}/apply",
            headers=headers,
        )
        assert applied_bad.status_code == 200, applied_bad.text
        applied_bad_json = applied_bad.json()
        assert applied_bad_json["decision"] == "held"
        assert any("above maximum" in reason for reason in applied_bad_json["reasons"])
        assert applied_bad_json["created_task_id"]

        tasks = client.get(
            "/api/v1/tasks",
            headers=headers,
            params={"queue": "manual-review", "status": "ready"},
        )
        assert tasks.status_code == 200, tasks.text
        assert any(item["focus_id"] == observation_bad_id for item in tasks.json()["items"])

        runs = client.get(
            f"/api/v1/autoverification/observations/{observation_bad_id}/runs",
            headers=headers,
        )
        assert runs.status_code == 200, runs.text
        assert len(runs.json()["items"]) >= 2


def test_autoverification_reference_and_delta_conditions(tmp_path):
    with make_client(tmp_path, "lis-autoverification-advanced.sqlite3") as client:
        headers, _ = bootstrap_admin(client)
        patient = create_patient(client, headers)

        catalog_response = client.post(
            "/api/v1/test-catalog",
            headers=headers,
            json={
                "local_code": "POT-ADV",
                "display_name": "Potassium advanced autoverify",
                "kind": "orderable",
                "loinc_num": "2823-3",
                "specimen_type_code": "SER",
                "default_ucum": "mmol/L",
                "result_value_type": "quantity",
            },
        )
        assert catalog_response.status_code == 201, catalog_response.text
        catalog = catalog_response.json()

        rule_response = client.post(
            "/api/v1/autoverification/rules",
            headers=headers,
            json={
                "name": "Advanced potassium chemistry rule",
                "priority": 5,
                "test_catalog_id": catalog["id"],
                "specimen_type_code": "SER",
                "condition": {
                    "specimen_status_in": ["accepted"],
                    "unit_ucum_equals": "mmol/L",
                    "require_reference_interval": True,
                    "require_within_reference_interval": True,
                    "disallow_reference_critical": True,
                    "disallow_interpretation_codes": ["H", "HH"],
                    "require_previous_final": True,
                    "delta_previous_max_age_hours": 24,
                    "delta_abs_max": 0.8,
                },
            },
        )
        assert rule_response.status_code == 201, rule_response.text

        old_order = create_order(client, headers, patient_id=patient["id"], catalog_id=catalog["id"])
        old_order_item_id = client.get(f"/api/v1/orders/{old_order['id']}", headers=headers).json()["items"][0]["id"]
        old_specimen = _accepted_specimen(
            client,
            headers,
            order_id=old_order["id"],
            patient_id=patient["id"],
            barcode="TUBE-AUTO-ADV-001",
        )
        previous_observation = client.post(
            "/api/v1/observations/manual",
            headers=headers,
            json={
                "order_item_id": old_order_item_id,
                "specimen_id": old_specimen["id"],
                "code_local": "POT-ADV",
                "code_loinc": "2823-3",
                "status": "final",
                "value_type": "quantity",
                "value_num": 4.2,
                "unit_ucum": "mmol/L",
                "effective_at": "2026-04-20T08:00:00Z",
                "reference_interval_snapshot": {"low": 3.5, "high": 5.1, "critical_high": 6.0},
            },
        )
        assert previous_observation.status_code == 201, previous_observation.text

        current_order = create_order(client, headers, patient_id=patient["id"], catalog_id=catalog["id"])
        current_order_item_id = client.get(f"/api/v1/orders/{current_order['id']}", headers=headers).json()["items"][0]["id"]
        current_specimen = _accepted_specimen(
            client,
            headers,
            order_id=current_order["id"],
            patient_id=patient["id"],
            barcode="TUBE-AUTO-ADV-002",
        )
        current_observation = client.post(
            "/api/v1/observations/manual",
            headers=headers,
            json={
                "order_item_id": current_order_item_id,
                "specimen_id": current_specimen["id"],
                "code_local": "POT-ADV",
                "code_loinc": "2823-3",
                "value_type": "quantity",
                "value_num": 6.3,
                "unit_ucum": "mmol/L",
                "interpretation_code": "H",
                "effective_at": "2026-04-23T09:00:00Z",
                "reference_interval_snapshot": {"low": 3.5, "high": 5.1, "critical_high": 6.0},
            },
        )
        assert current_observation.status_code == 201, current_observation.text
        current_observation_id = current_observation.json()["id"]

        evaluated = client.post(
            f"/api/v1/autoverification/observations/{current_observation_id}/evaluate",
            headers=headers,
        )
        assert evaluated.status_code == 200, evaluated.text
        evaluated_json = evaluated.json()
        assert evaluated_json["overall_decision"] == "fail"
        reasons = evaluated_json["rules"][0]["reasons"]
        assert any("above reference high" in reason for reason in reasons)
        assert any("reference critical high" in reason for reason in reasons)
        assert any("interpretation code 'H' is disallowed" == reason for reason in reasons)
        assert any("exceeds delta max age 24h" in reason for reason in reasons)
        assert any("absolute delta" in reason for reason in reasons)

        applied = client.post(
            f"/api/v1/autoverification/observations/{current_observation_id}/apply",
            headers=headers,
        )
        assert applied.status_code == 200, applied.text
        assert applied.json()["decision"] == "held"
