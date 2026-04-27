from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from tests.support import (
    bootstrap_admin,
    create_catalog_item,
    create_order,
    create_patient,
    create_user,
    login,
    make_client,
)


def test_order_workflow_persists_and_updates_status(tmp_path):
    with make_client(tmp_path, "lis-orders.sqlite3") as client:
        headers, _ = bootstrap_admin(client)
        patient = create_patient(client, headers)
        first_catalog = create_catalog_item(client, headers)
        second_catalog = create_catalog_item(client, headers)

        created_order = create_order(
            client,
            headers,
            patient_id=patient["id"],
            catalog_id=first_catalog["id"],
        )

        detail_response = client.get(f"/api/v1/orders/{created_order['id']}", headers=headers)
        assert detail_response.status_code == 200
        detail_payload = detail_response.json()
        assert detail_payload["status"] == "registered"
        assert len(detail_payload["items"]) == 1

        add_item_response = client.post(
            f"/api/v1/orders/{created_order['id']}/items",
            headers=headers,
            json={"test_catalog_id": second_catalog["id"]},
        )
        assert add_item_response.status_code == 201

        first_item_id = detail_payload["items"][0]["id"]
        hold_response = client.post(
            f"/api/v1/order-items/{first_item_id}/hold",
            headers=headers,
            json={"reason": "Awaiting clarification"},
        )
        assert hold_response.status_code == 200
        assert hold_response.json()["status"] == "on_hold"

        updated_detail = client.get(f"/api/v1/orders/{created_order['id']}", headers=headers).json()
        assert updated_detail["status"] == "on_hold"
        assert len(updated_detail["items"]) == 2


def test_specimen_lifecycle_and_trace(tmp_path):
    with make_client(tmp_path, "lis-specimens.sqlite3") as client:
        headers, _ = bootstrap_admin(client)
        patient = create_patient(client, headers)
        catalog = create_catalog_item(client, headers)
        order = create_order(
            client,
            headers,
            patient_id=patient["id"],
            catalog_id=catalog["id"],
            priority="urgent",
        )

        accession_response = client.post(
            "/api/v1/specimens/accession",
            headers=headers,
            json={
                "order_id": order["id"],
                "patient_id": patient["id"],
                "specimen_type_code": "serum",
            },
        )
        assert accession_response.status_code == 201
        specimen = accession_response.json()
        specimen_id = specimen["id"]
        assert specimen["status"] == "expected"

        collect_response = client.post(
            f"/api/v1/specimens/{specimen_id}/collect",
            headers=headers,
            json={"collected_at": datetime.now(UTC).isoformat(), "container_barcodes": ["TUBE-001"]},
        )
        assert collect_response.status_code == 200
        assert collect_response.json()["status"] == "collected"

        receive_response = client.post(
            f"/api/v1/specimens/{specimen_id}/receive",
            headers=headers,
            json={"received_at": datetime.now(UTC).isoformat()},
        )
        assert receive_response.status_code == 200
        assert receive_response.json()["status"] == "received"

        accept_response = client.post(f"/api/v1/specimens/{specimen_id}/accept", headers=headers)
        assert accept_response.status_code == 200
        assert accept_response.json()["status"] == "accepted"

        trace_response = client.get(f"/api/v1/specimens/{specimen_id}/trace", headers=headers)
        assert trace_response.status_code == 200
        trace = trace_response.json()
        assert [event["event_type"] for event in trace["events"]] == [
            "accessioned",
            "collected",
            "received",
            "accepted",
        ]

        list_response = client.get(
            "/api/v1/specimens",
            headers=headers,
            params={"patient_id": patient["id"], "status": "accepted"},
        )
        assert list_response.status_code == 200
        assert len(list_response.json()["items"]) == 1


def test_task_workflow_transitions(tmp_path):
    with make_client(tmp_path, "lis-tasks.sqlite3") as client:
        headers, user = bootstrap_admin(client)
        patient = create_patient(client, headers)
        catalog = create_catalog_item(client, headers)
        order = create_order(
            client,
            headers,
            patient_id=patient["id"],
            catalog_id=catalog["id"],
            priority="stat",
        )
        order_detail = client.get(f"/api/v1/orders/{order['id']}", headers=headers).json()
        order_item_id = order_detail["items"][0]["id"]

        create_task_response = client.post(
            "/api/v1/tasks",
            headers=headers,
            json={
                "focus_type": "order-item",
                "focus_id": order_item_id,
                "based_on_order_item_id": order_item_id,
                "queue_code": "chemistry",
                "status": "ready",
                "inputs": {"priority_hint": "bench-1"},
            },
        )
        assert create_task_response.status_code == 201
        task = create_task_response.json()
        task_id = task["id"]

        claim_response = client.post(
            f"/api/v1/tasks/{task_id}/claim",
            headers=headers,
            json={"owner_user_id": user["id"]},
        )
        assert claim_response.status_code == 200
        assert claim_response.json()["business_status"] == "claimed"

        start_response = client.post(f"/api/v1/tasks/{task_id}/start", headers=headers)
        assert start_response.status_code == 200
        assert start_response.json()["status"] == "in_progress"

        complete_response = client.post(
            f"/api/v1/tasks/{task_id}/complete",
            headers=headers,
            json={"outputs": {"result_batch": "B-001"}},
        )
        assert complete_response.status_code == 200
        assert complete_response.json()["status"] == "completed"

        list_response = client.get(
            "/api/v1/tasks",
            headers=headers,
            params={"queue": "chemistry", "status": "completed"},
        )
        assert list_response.status_code == 200
        assert len(list_response.json()["items"]) == 1


def test_viewer_cannot_create_patient(tmp_path):
    with make_client(tmp_path, "lis-rbac.sqlite3") as client:
        bootstrap_admin(client)
        viewer_username = f"viewer-{uuid4().hex[:8]}"
        create_user(
            client,
            username=viewer_username,
            password="viewer12345",
            display_name="Viewer User",
            role_code="viewer",
        )
        viewer_headers, _ = login(
            client,
            username=viewer_username,
            password="viewer12345",
        )
        response = client.post(
            "/api/v1/patients",
            headers=viewer_headers,
            json={
                "mrn": f"MRN-{uuid4().hex[:8].upper()}",
                "given_name": "Jan",
                "family_name": "Kowalski",
            },
        )
        assert response.status_code == 403


def test_report_listing_returns_generated_report(tmp_path):
    with make_client(tmp_path, "lis-report-list.sqlite3") as client:
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

        observation_response = client.post(
            "/api/v1/observations/manual",
            headers=headers,
            json={
                "order_item_id": order_item_id,
                "code_local": "GLU",
                "status": "preliminary",
                "value_type": "quantity",
                "value_num": 105.4,
                "unit_ucum": "mg/dL",
            },
        )
        assert observation_response.status_code == 201

        report_response = client.post(
            "/api/v1/reports/generate",
            headers=headers,
            json={"order_id": order["id"], "conclusion_text": "Initial release"},
        )
        assert report_response.status_code == 201
        report = report_response.json()

        list_response = client.get(
            "/api/v1/reports",
            headers=headers,
            params={"patient_id": patient["id"], "status": "preliminary"},
        )
        assert list_response.status_code == 200
        assert list_response.json()["items"][0]["id"] == report["id"]
