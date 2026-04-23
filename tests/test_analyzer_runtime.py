from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.db.models import AnalyzerTransportSessionRecord
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


def test_analyzer_runtime_worker_respects_active_and_expired_lease(tmp_path):
    with make_client(tmp_path, "lis-runtime-lease.sqlite3") as client:
        headers, _ = bootstrap_admin(client)

        device = client.post(
            "/api/v1/devices",
            headers=headers,
            json={
                "code": "ASTM-RUNTIME-LEASE-01",
                "display_name": "Runtime lease analyzer",
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
                "logical_payload": r"H|\^&|||ASTM-RUNTIME-LEASE-01|||||P|1\rL|1|N\r",
            },
        )
        assert queued.status_code == 201, queued.text

        with client.app.state.db.session_factory() as session:
            transport_session = session.get(AnalyzerTransportSessionRecord, session_id)
            assert transport_session is not None
            transport_session.lease_owner = "other-worker"
            transport_session.lease_acquired_at = datetime.now(UTC)
            transport_session.lease_expires_at = datetime.now(UTC) + timedelta(seconds=30)
            session.commit()

        worker = AnalyzerRuntimeWorker(
            client.app.state.db.session_factory,
            worker_id="runtime-worker-a",
            lease_timeout_seconds=10,
        )
        mock_connector = MockAnalyzerConnector(label="runtime-lease")
        worker.register_connector(profile_id, mock_connector)
        try:
            skipped = worker.run_once(profile_id=profile_id)
            assert skipped.lease_skipped == 1
            assert skipped.sessions_touched == 0
            assert mock_connector.outbound_payloads == []

            with client.app.state.db.session_factory() as session:
                transport_session = session.get(AnalyzerTransportSessionRecord, session_id)
                assert transport_session is not None
                transport_session.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
                session.commit()

            claimed = worker.run_once(profile_id=profile_id)
            assert claimed.leases_acquired == 1
            assert claimed.sessions_touched == 1
            assert mock_connector.outbound_payloads[-1] == transport_service.ENQ

            with client.app.state.db.session_factory() as session:
                transport_session = session.get(AnalyzerTransportSessionRecord, session_id)
                assert transport_session is not None
                assert transport_session.lease_owner == "runtime-worker-a"
        finally:
            worker.close()


def test_analyzer_runtime_worker_applies_backoff_after_error(tmp_path):
    class FailingConnector:
        def __init__(self) -> None:
            self.closed = False

        def open(self) -> None:
            raise RuntimeError("synthetic-open-failure")

        def close(self) -> None:
            self.closed = True

        def is_open(self) -> bool:
            return False

        def read(self, *, timeout_seconds: float) -> str | None:
            return None

        def write(self, payload: str, *, timeout_seconds: float) -> None:
            return None

        def describe(self) -> str:
            return "failing"

    with make_client(tmp_path, "lis-runtime-backoff.sqlite3") as client:
        headers, _ = bootstrap_admin(client)

        device = client.post(
            "/api/v1/devices",
            headers=headers,
            json={
                "code": "ASTM-RUNTIME-BACKOFF-01",
                "display_name": "Runtime backoff analyzer",
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

        worker = AnalyzerRuntimeWorker(
            client.app.state.db.session_factory,
            worker_id="runtime-worker-backoff",
            lease_timeout_seconds=10,
            retry_backoff_seconds=30,
            retry_backoff_max_seconds=30,
        )
        failing_connector = FailingConnector()
        worker.register_connector(profile_id, failing_connector)
        try:
            first = worker.run_once(profile_id=profile_id)
            assert len(first.errors) == 1

            with client.app.state.db.session_factory() as session:
                transport_session = session.get(AnalyzerTransportSessionRecord, session_id)
                assert transport_session is not None
                assert transport_session.session_status == "error"
                assert transport_session.failure_count == 1
                assert transport_session.next_retry_at is not None
                next_retry_at = transport_session.next_retry_at

            second = worker.run_once(profile_id=profile_id)
            assert second.backoff_skipped == 1
            assert second.errors == []

            with client.app.state.db.session_factory() as session:
                transport_session = session.get(AnalyzerTransportSessionRecord, session_id)
                assert transport_session is not None
                assert transport_session.failure_count == 1
                assert transport_session.next_retry_at == next_retry_at
        finally:
            worker.close()


def test_analyzer_transport_runtime_overview_reports_leases_and_backoff(tmp_path):
    with make_client(tmp_path, "lis-runtime-overview.sqlite3") as client:
        headers, _ = bootstrap_admin(client)

        device = client.post(
            "/api/v1/devices",
            headers=headers,
            json={
                "code": "ASTM-RUNTIME-OVERVIEW-01",
                "display_name": "Runtime overview analyzer",
                "protocol": "astm",
            },
        )
        assert device.status_code == 201, device.text
        device_id = device.json()["id"]

        profile = _create_mock_profile(client, headers, device_id=device_id, auto_dispatch_astm=False)
        profile_id = profile["id"]

        session_a = client.post(
            "/api/v1/analyzer-transport/sessions",
            headers=headers,
            json={"device_id": device_id, "profile_id": profile_id},
        )
        assert session_a.status_code == 201, session_a.text

        session_b = client.post(
            "/api/v1/analyzer-transport/sessions",
            headers=headers,
            json={"device_id": device_id, "profile_id": profile_id},
        )
        assert session_b.status_code == 201, session_b.text

        session_a_id = session_a.json()["id"]
        session_b_id = session_b.json()["id"]

        with client.app.state.db.session_factory() as session:
            leased = session.get(AnalyzerTransportSessionRecord, session_a_id)
            backoff = session.get(AnalyzerTransportSessionRecord, session_b_id)
            assert leased is not None and backoff is not None

            leased.lease_owner = "worker-lease"
            leased.lease_acquired_at = datetime.now(UTC)
            leased.lease_expires_at = datetime.now(UTC) + timedelta(seconds=30)
            leased.heartbeat_at = datetime.now(UTC)

            backoff.session_status = "error"
            backoff.failure_count = 2
            backoff.next_retry_at = datetime.now(UTC) + timedelta(seconds=45)
            backoff.last_error = "synthetic-error"
            session.commit()

        overview = client.get(
            "/api/v1/analyzer-transport/runtime/overview",
            headers=headers,
            params={"device_id": device_id},
        )
        assert overview.status_code == 200, overview.text
        payload = overview.json()
        assert payload["profile_count"] == 1
        assert payload["session_count"] == 2
        assert payload["leased_session_count"] == 1
        assert payload["stale_lease_count"] == 0
        assert payload["backoff_session_count"] == 1
        assert payload["error_session_count"] == 1
        assert len(payload["items"]) == 2
