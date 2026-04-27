from __future__ import annotations

from datetime import UTC, datetime

from tests.support import bootstrap_admin, create_catalog_item, create_order, create_patient, make_client


def test_root_serves_html_for_browser_and_json_for_api_clients(tmp_path):
    with make_client(tmp_path, "lis-dashboard-root.sqlite3") as client:
        browser_response = client.get("/", headers={"Accept": "text/html"})
        assert browser_response.status_code == 200
        assert "text/html" in browser_response.headers["content-type"]
        assert "LIS Core Workbench" in browser_response.text

        api_response = client.get("/", headers={"Accept": "application/json"})
        assert api_response.status_code == 200
        assert api_response.json()["service"] == "lis-core"
        assert api_response.json()["ui"] == "/dashboard"


def test_dashboard_overview_returns_live_operational_data(tmp_path):
    with make_client(tmp_path, "lis-dashboard-overview.sqlite3") as client:
        headers, user = bootstrap_admin(client)
        patient = create_patient(client, headers)
        catalog = create_catalog_item(client, headers)
        order = create_order(client, headers, patient_id=patient["id"], catalog_id=catalog["id"])

        order_detail = client.get(f"/api/v1/orders/{order['id']}", headers=headers).json()
        order_item_id = order_detail["items"][0]["id"]

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

        task_response = client.post(
            "/api/v1/tasks",
            headers=headers,
            json={
                "focus_type": "order-item",
                "focus_id": order_item_id,
                "based_on_order_item_id": order_item_id,
                "queue_code": "chemistry",
                "status": "ready",
                "owner_user_id": user["id"],
                "due_at": datetime.now(UTC).isoformat(),
            },
        )
        assert task_response.status_code == 201

        overview_response = client.get("/api/v1/dashboard/overview", headers=headers)
        assert overview_response.status_code == 200
        payload = overview_response.json()

        metrics = {metric["key"]: metric["value"] for metric in payload["metrics"]}
        assert metrics["patients"] == 1
        assert metrics["orders"] == 1
        assert metrics["specimens"] == 1
        assert metrics["open_tasks"] == 1
        assert payload["database_status"] == "ok"
        assert payload["task_queues"][0]["queue_code"] == "chemistry"
        assert payload["recent_orders"][0]["label"] == order["requisition_no"]
        assert payload["recent_specimens"][0]["status"] == "expected"
        assert payload["recent_tasks"][0]["status"] == "ready"
