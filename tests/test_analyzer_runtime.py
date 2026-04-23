from __future__ import annotations

from datetime import UTC, datetime

from app.services import analyzer_transport as transport_service
from app.services.analyzer_runtime import AnalyzerRuntimeWorker, MockAnalyzerConnector
from tests.support import bootstrap_admin, create_order, create_patient, make_client


def _create_mock_profile(client, headers: dict[str, str], *, device_id: str, auto_dispatch_astm: bool = True, auto_verify: bool = False):
    response = client.post(
        "/api/v1/analyzer-transport/profiles",
        headers=headers,
        json={
            "device_id": device_id,
            "connection_mode": "mock",
            "frame_payload_size": 1000,
            "read_timeout_seconds": 0,
            "write_timeout_seconds": 0,
            "auto_dispatch_astm": auto_dispatch_astm,
            "auto_verify": auto_verify,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_analyzer_runtime_worker_drives_outbound_flow(tmp_path):
    with make_client(tmp_path, "lis-runtime-outbound.sqlite3") as client:
        headers, _ = bootstrap_admin(client)

        device = client.post(
            "/api/v1/devices",
            headers=headers,
            json={
                "code": "ASTM-RUNTIME-OUT-01",
                "display_name": "Runtime outbound analyzer",
                "protocol": "astm",
            },
        )
        assert device.status_code == 201, device.text
        device_id = device.json()["id"]

        profile = _create_mock_profile(client, headers, device_id=device_id, auto_dispatch_astm=False)
        profile_id = profile["id"]

        opened = client.post(
            "/api/v1/analyzer-transport/sessions",
            headers=headers,
            json={"device_id": device_id, "profile_id": profile_id},
        )
        assert opened.status_code == 201, opened.text
        session_id = opened.json()["id"]

        queued = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/queue-outbound",
            headers=headers,
            json={
                "message_type": "ASTM-WORKLIST",
                "logical_payload": r"H|\^&|||ASTM-RUNTIME-OUT-01|||||P|1\rL|1|N\r",
            },
        )
        assert queued.status_code == 201, queued.text
        message_id = queued.json()["id"]

        worker = AnalyzerRuntimeWorker(client.app.state.db.session_factory)
        mock_connector = MockAnalyzerConnector(label="runtime-outbound")
        worker.register_connector(profile_id, mock_connector)
        try:
            worker.run_once(profile_id=profile_id)
            assert mock_connector.outbound_payloads[-1] == transport_service.ENQ

            mock_connector.enqueue_inbound(transport_service.ACK)
            worker.run_once(profile_id=profile_id)
            assert mock_connector.outbound_payloads[-1].startswith(transport_service.STX)

            mock_connector.enqueue_inbound(transport_service.ACK)
            worker.run_once(profile_id=profile_id)
            assert mock_connector.outbound_payloads[-1] == transport_service.EOT

            mock_connector.enqueue_inbound(transport_service.ACK)
            stats = worker.run_once(profile_id=profile_id)
            assert stats.errors == []

            messages = client.get(
                f"/api/v1/analyzer-transport/sessions/{session_id}/messages",
                headers=headers,
            )
            assert messages.status_code == 200, messages.text
            assert messages.json()["items"][0]["id"] == message_id
            assert messages.json()["items"][0]["transport_status"] == "completed"
        finally:
            worker.close()


def test_analyzer_runtime_worker_dispatches_inbound_astm(tmp_path):
    with make_client(tmp_path, "lis-runtime-inbound.sqlite3") as client:
        headers, _ = bootstrap_admin(client)
        patient = create_patient(client, headers)

        catalog = client.post(
            "/api/v1/test-catalog",
            headers=headers,
            json={
                "local_code": "GLU-RUNTIME",
                "display_name": "Runtime glucose",
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
            headers=headers,
            json={
                "code": "ASTM-RUNTIME-IN-01",
                "display_name": "Runtime inbound analyzer",
                "protocol": "astm",
            },
        )
        assert device.status_code == 201, device.text
        device_id = device.json()["id"]

        mapping = client.post(
            f"/api/v1/devices/{device_id}/mappings",
            headers=headers,
            json={
                "incoming_test_code": "GLU-RUNTIME",
                "test_catalog_id": catalog_id,
                "default_unit_ucum": "mg/dL",
            },
        )
        assert mapping.status_code == 201, mapping.text

        rule = client.post(
            "/api/v1/autoverification/rules",
            headers=headers,
            json={
                "name": "Runtime autoverify",
                "test_catalog_id": catalog_id,
                "device_id": device_id,
                "condition": {
                    "specimen_status_in": ["accepted", "in_process"],
                    "unit_ucum_equals": "mg/dL",
                    "numeric_min": 60,
                    "numeric_max": 150,
                },
            },
        )
        assert rule.status_code == 201, rule.text

        order = create_order(
            client,
            headers,
            patient_id=patient["id"],
            catalog_id=catalog_id,
        )
        order_detail = client.get(f"/api/v1/orders/{order['id']}", headers=headers)
        assert order_detail.status_code == 200, order_detail.text
        order_item_id = order_detail.json()["items"][0]["id"]

        specimen = client.post(
            "/api/v1/specimens/accession",
            headers=headers,
            json={
                "order_id": order["id"],
                "patient_id": patient["id"],
                "specimen_type_code": "SER",
            },
        )
        assert specimen.status_code == 201, specimen.text
        specimen_id = specimen.json()["id"]
        accession_no = specimen.json()["accession_no"]

        assert client.post(
            f"/api/v1/specimens/{specimen_id}/collect",
            headers=headers,
            json={
                "collected_at": datetime.now(UTC).isoformat(),
                "container_barcodes": ["TUBE-RUNTIME-001"],
            },
        ).status_code == 200
        assert client.post(
            f"/api/v1/specimens/{specimen_id}/receive",
            headers=headers,
            json={"received_at": datetime.now(UTC).isoformat()},
        ).status_code == 200
        assert client.post(
            f"/api/v1/specimens/{specimen_id}/accept",
            headers=headers,
        ).status_code == 200

        profile = _create_mock_profile(
            client,
            headers,
            device_id=device_id,
            auto_dispatch_astm=True,
            auto_verify=True,
        )
        profile_id = profile["id"]

        worker = AnalyzerRuntimeWorker(client.app.state.db.session_factory)
        mock_connector = MockAnalyzerConnector(label="runtime-inbound")
        worker.register_connector(profile_id, mock_connector)
        try:
            astm_message = "\r".join(
                [
                    r"H|\^&|||ASTM-RUNTIME-IN-01|||||P|1",
                    "P|1||MRN-RUNTIME-1||Runtime^Anna",
                    f"O|1|{accession_no}||GLU-RUNTIME^Runtime glucose|R",
                    "R|1|GLU-RUNTIME^Runtime glucose|99.5|mg/dL|N||F|20260423113000",
                    "L|1|N",
                    "",
                ]
            )
            frame = transport_service.frame_astm_message(astm_message, frame_payload_size=1000)[0][
                "framed_payload"
            ]
            mock_connector.enqueue_inbound(
                transport_service.ENQ,
                frame,
                transport_service.EOT,
            )

            stats = worker.run_once(profile_id=profile_id)
            assert stats.errors == []
            assert stats.dispatches == 1
            assert mock_connector.outbound_payloads.count(transport_service.ACK) >= 2

            session = client.app.state.db.session_factory()
            try:
                raw_messages = client.get(
                    "/api/v1/integrations/device-gateway/messages",
                    headers=headers,
                    params={"device_id": device_id},
                )
                assert raw_messages.status_code == 200, raw_messages.text
                assert len(raw_messages.json()["items"]) == 1

                observations = client.get(
                    "/api/v1/observations",
                    headers=headers,
                    params={"specimen_id": specimen_id},
                )
                assert observations.status_code == 200, observations.text
                created = observations.json()["items"][0]
                assert created["order_item_id"] == order_item_id
                assert created["status"] == "final"
            finally:
                session.close()
        finally:
            worker.close()
