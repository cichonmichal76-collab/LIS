from __future__ import annotations

import os
from datetime import UTC, datetime

from _smoke_support import make_smoke_client
from app.services import analyzer_transport as transport_service
from app.services.analyzer_runtime import AnalyzerRuntimeWorker, MockAnalyzerConnector


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    os.environ.pop("LIS_DATABASE_URL", None)

    with make_smoke_client("smoke_test_runtime") as client:
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

        patient = client.post(
            "/api/v1/patients",
            headers=auth_headers,
            json={
                "mrn": "MRN-RUNTIME-SMOKE-001",
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
                "local_code": "GLU-RUNTIME-SMOKE",
                "display_name": "Glucose runtime smoke",
                "kind": "orderable",
                "loinc_num": "2345-7",
                "specimen_type_code": "SER",
                "default_ucum": "mg/dL",
                "result_value_type": "quantity",
            },
        )
        assert catalog.status_code == 201, catalog.text
        catalog_id = catalog.json()["id"]

        device = client.post(
            "/api/v1/devices",
            headers=auth_headers,
            json={
                "code": "ASTM-RUNTIME-SMOKE-01",
                "display_name": "Runtime smoke analyzer",
                "protocol": "astm",
            },
        )
        assert device.status_code == 201, device.text
        device_id = device.json()["id"]

        assert client.post(
            f"/api/v1/devices/{device_id}/mappings",
            headers=auth_headers,
            json={
                "incoming_test_code": "GLU-RUNTIME-SMOKE",
                "test_catalog_id": catalog_id,
                "default_unit_ucum": "mg/dL",
            },
        ).status_code == 201

        assert client.post(
            "/api/v1/autoverification/rules",
            headers=auth_headers,
            json={
                "name": "Runtime smoke autoverify",
                "test_catalog_id": catalog_id,
                "device_id": device_id,
                "condition": {
                    "specimen_status_in": ["accepted", "in_process"],
                    "unit_ucum_equals": "mg/dL",
                    "numeric_min": 60,
                    "numeric_max": 150,
                },
            },
        ).status_code == 201

        order = client.post(
            "/api/v1/orders",
            headers=auth_headers,
            json={
                "patient_id": patient_id,
                "source_system": "runtime-smoke",
                "priority": "routine",
                "ordered_at": datetime.now(UTC).isoformat(),
                "items": [{"test_catalog_id": catalog_id, "requested_specimen_type_code": "SER"}],
            },
        )
        assert order.status_code == 201, order.text
        order_id = order.json()["id"]
        order_detail = client.get(f"/api/v1/orders/{order_id}", headers=auth_headers)
        assert order_detail.status_code == 200, order_detail.text
        order_item_id = order_detail.json()["items"][0]["id"]

        specimen = client.post(
            "/api/v1/specimens/accession",
            headers=auth_headers,
            json={
                "order_id": order_id,
                "patient_id": patient_id,
                "specimen_type_code": "SER",
            },
        )
        assert specimen.status_code == 201, specimen.text
        specimen_id = specimen.json()["id"]
        accession_no = specimen.json()["accession_no"]

        assert client.post(
            f"/api/v1/specimens/{specimen_id}/collect",
            headers=auth_headers,
            json={
                "collected_at": datetime.now(UTC).isoformat(),
                "container_barcodes": ["TUBE-RUNTIME-SMOKE-001"],
            },
        ).status_code == 200
        assert client.post(
            f"/api/v1/specimens/{specimen_id}/receive",
            headers=auth_headers,
            json={"received_at": datetime.now(UTC).isoformat()},
        ).status_code == 200
        assert client.post(f"/api/v1/specimens/{specimen_id}/accept", headers=auth_headers).status_code == 200

        profile = client.post(
            "/api/v1/analyzer-transport/profiles",
            headers=auth_headers,
            json={
                "device_id": device_id,
                "connection_mode": "mock",
                "frame_payload_size": 1000,
                "read_timeout_seconds": 0,
                "write_timeout_seconds": 0,
                "auto_dispatch_astm": True,
                "auto_verify": True,
            },
        )
        assert profile.status_code == 201, profile.text
        profile_id = profile.json()["id"]

        worker = AnalyzerRuntimeWorker(client.app.state.db.session_factory)
        connector = MockAnalyzerConnector(label="runtime-smoke")
        worker.register_connector(profile_id, connector)
        try:
            astm_message = "\r".join(
                [
                    r"H|\^&|||ASTM-RUNTIME-SMOKE-01|||||P|1",
                    "P|1||MRN-RUNTIME-SMOKE-001||Nowak^Anna",
                    f"O|1|{accession_no}||GLU-RUNTIME-SMOKE^Glucose runtime smoke|R",
                    "R|1|GLU-RUNTIME-SMOKE^Glucose runtime smoke|97.7|mg/dL|N||F|20260423124500",
                    "L|1|N",
                    "",
                ]
            )
            frame = transport_service.frame_astm_message(astm_message, frame_payload_size=1000)[0][
                "framed_payload"
            ]
            connector.enqueue_inbound(
                transport_service.ENQ,
                frame,
                transport_service.EOT,
            )

            stats = worker.run_once(profile_id=profile_id)
            assert stats.dispatches == 1
            assert stats.errors == []

            overview = client.get(
                "/api/v1/analyzer-transport/runtime/overview",
                headers=auth_headers,
                params={"device_id": device_id},
            )
            assert overview.status_code == 200, overview.text
            overview_payload = overview.json()
            assert overview_payload["profile_count"] == 1
            assert overview_payload["session_count"] == 1
            assert overview_payload["leased_session_count"] == 1

            observations = client.get(
                "/api/v1/observations",
                headers=auth_headers,
                params={"specimen_id": specimen_id},
            )
            assert observations.status_code == 200, observations.text
            observation = observations.json()["items"][0]
            assert observation["order_item_id"] == order_item_id
            assert observation["status"] == "final"
        finally:
            worker.close()

        print("Analyzer runtime smoke OK")
        print(
            {
                "device_id": device_id,
                "profile_id": profile_id,
                "order_id": order_id,
                "specimen_id": specimen_id,
            }
        )


if __name__ == "__main__":
    main()
