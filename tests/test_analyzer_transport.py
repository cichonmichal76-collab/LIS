from __future__ import annotations

from datetime import UTC, datetime

from app.services.analyzer_transport import frame_astm_message
from tests.support import bootstrap_admin, create_order, create_patient, make_client


def test_analyzer_transport_outbound_ack_retry_flow(tmp_path):
    with make_client(tmp_path, "lis-transport-outbound.sqlite3") as client:
        headers, _ = bootstrap_admin(client)

        device = client.post(
            "/api/v1/devices",
            headers=headers,
            json={
                "code": "ASTM-TX-01",
                "display_name": "Transport analyzer",
                "protocol": "astm",
            },
        )
        assert device.status_code == 201, device.text
        device_id = device.json()["id"]

        profile = client.post(
            "/api/v1/analyzer-transport/profiles",
            headers=headers,
            json={
                "device_id": device_id,
                "frame_payload_size": 64,
                "ack_timeout_seconds": 10,
                "max_retries": 2,
            },
        )
        assert profile.status_code == 201, profile.text

        session = client.post(
            "/api/v1/analyzer-transport/sessions",
            headers=headers,
            json={"device_id": device_id},
        )
        assert session.status_code == 201, session.text
        session_id = session.json()["id"]

        queued = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/queue-outbound",
            headers=headers,
            json={
                "message_type": "ASTM-WORKLIST",
                "logical_payload": r"H|\^&|||ASTM-TX-01|||||P|1\rL|1|N\r",
            },
        )
        assert queued.status_code == 201, queued.text
        message_id = queued.json()["id"]

        send_1 = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/next",
            headers=headers,
        )
        assert send_1.status_code == 200, send_1.text
        assert send_1.json()["transport_item"]["control_code"] == "ENQ"

        ack_enq = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/ack",
            headers=headers,
        )
        assert ack_enq.status_code == 200, ack_enq.text
        assert ack_enq.json()["decision"] == "acknowledged"

        send_frame = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/next",
            headers=headers,
        )
        assert send_frame.status_code == 200, send_frame.text
        frame_item = send_frame.json()["transport_item"]
        assert frame_item["kind"] == "frame"
        assert frame_item["frame_no"] == 1

        nak = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/nak",
            headers=headers,
        )
        assert nak.status_code == 200, nak.text
        assert nak.json()["decision"] == "resend"
        assert nak.json()["message"]["retry_count"] == 1

        resend = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/next",
            headers=headers,
        )
        assert resend.status_code == 200, resend.text
        resent_item = resend.json()["transport_item"]
        assert resent_item["kind"] == "frame"
        assert resent_item["payload_escaped"] == frame_item["payload_escaped"]
        assert resent_item["retry_count"] == 1

        ack_frame = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/ack",
            headers=headers,
        )
        assert ack_frame.status_code == 200, ack_frame.text

        send_eot = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/next",
            headers=headers,
        )
        assert send_eot.status_code == 200, send_eot.text
        assert send_eot.json()["transport_item"]["control_code"] == "EOT"

        ack_eot = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/ack",
            headers=headers,
        )
        assert ack_eot.status_code == 200, ack_eot.text
        assert ack_eot.json()["message"]["transport_status"] == "completed"
        assert ack_eot.json()["session"]["session_status"] == "idle"

        messages = client.get(
            f"/api/v1/analyzer-transport/sessions/{session_id}/messages",
            headers=headers,
        )
        assert messages.status_code == 200, messages.text
        assert messages.json()["items"][0]["id"] == message_id
        assert messages.json()["items"][0]["transport_status"] == "completed"

        frames = client.get(
            f"/api/v1/analyzer-transport/sessions/{session_id}/frames",
            headers=headers,
        )
        assert frames.status_code == 200, frames.text
        control_codes = [
            row["control_code"]
            for row in frames.json()["items"]
            if row["event_kind"] == "control"
        ]
        assert "ENQ" in control_codes
        assert "ACK" in control_codes
        assert "NAK" in control_codes


def test_analyzer_transport_inbound_duplicate_and_dispatch(tmp_path):
    with make_client(tmp_path, "lis-transport-dispatch.sqlite3") as client:
        headers, _ = bootstrap_admin(client)
        patient = create_patient(client, headers)

        catalog = client.post(
            "/api/v1/test-catalog",
            headers=headers,
            json={
                "local_code": "GLU-TX",
                "display_name": "Glucose transport",
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
                "code": "ASTM-TX-DISP",
                "display_name": "Analyzer transport dispatch",
                "protocol": "astm",
            },
        )
        assert device.status_code == 201, device.text
        device_id = device.json()["id"]

        mapping = client.post(
            f"/api/v1/devices/{device_id}/mappings",
            headers=headers,
            json={
                "incoming_test_code": "GLU-TX",
                "test_catalog_id": catalog_id,
                "default_unit_ucum": "mg/dL",
            },
        )
        assert mapping.status_code == 201, mapping.text

        rule = client.post(
            "/api/v1/autoverification/rules",
            headers=headers,
            json={
                "name": "Transport glucose autoverify",
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
                "container_barcodes": ["TUBE-TX-001"],
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

        profile = client.post(
            "/api/v1/analyzer-transport/profiles",
            headers=headers,
            json={"device_id": device_id, "frame_payload_size": 1000},
        )
        assert profile.status_code == 201, profile.text

        transport_session = client.post(
            "/api/v1/analyzer-transport/sessions",
            headers=headers,
            json={"device_id": device_id},
        )
        assert transport_session.status_code == 201, transport_session.text
        session_id = transport_session.json()["id"]

        enq = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/inbound/control",
            headers=headers,
            json={"control_code": "ENQ"},
        )
        assert enq.status_code == 200, enq.text
        assert enq.json()["reply_control_code"] == "ACK"
        message_id = enq.json()["message"]["id"]

        astm_message = "\r".join(
            [
                r"H|\^&|||ASTM-TX-DISP|||||P|1",
                "P|1||MRN-TX-1||Transport^Anna",
                f"O|1|{accession_no}||GLU-TX^Glucose transport|R",
                "R|1|GLU-TX^Glucose transport|98.8|mg/dL|N||F|20260422112900",
                "L|1|N",
                "",
            ]
        )
        frame = frame_astm_message(astm_message, frame_payload_size=1000)[0]["framed_payload_escaped"]

        inbound = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/inbound/frame",
            headers=headers,
            json={
                "framed_payload": frame,
                "auto_dispatch_astm": True,
                "auto_verify": True,
            },
        )
        assert inbound.status_code == 200, inbound.text
        inbound_json = inbound.json()
        assert inbound_json["reply_control_code"] == "ACK"
        assert inbound_json["assembled"] is True
        assert inbound_json["dispatch"]["raw_message_id"]
        created = inbound_json["dispatch"]["created_observations"][0]
        assert created["status"] == "final"
        assert created["autoverification"]["decision"] == "auto_finalized"
        assert created["order_item_id"] == order_item_id

        duplicate = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/inbound/frame",
            headers=headers,
            json={"framed_payload": frame},
        )
        assert duplicate.status_code == 200, duplicate.text
        assert duplicate.json()["duplicate"] is True
        assert duplicate.json()["reply_control_code"] == "ACK"

        eot = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/inbound/control",
            headers=headers,
            json={"control_code": "EOT"},
        )
        assert eot.status_code == 200, eot.text
        assert eot.json()["session"]["session_status"] == "idle"

        frames = client.get(
            f"/api/v1/analyzer-transport/sessions/{session_id}/frames",
            headers=headers,
            params={"message_id": message_id},
        )
        assert frames.status_code == 200, frames.text
        duplicates = [row for row in frames.json()["items"] if row["duplicate_flag"] is True]
        assert len(duplicates) == 1


def test_analyzer_transport_dead_letter_and_requeue_failed_outbound(tmp_path):
    with make_client(tmp_path, "lis-transport-dead-letter.sqlite3") as client:
        headers, _ = bootstrap_admin(client)

        device = client.post(
            "/api/v1/devices",
            headers=headers,
            json={
                "code": "ASTM-TX-DLQ-01",
                "display_name": "Transport dead-letter analyzer",
                "protocol": "astm",
            },
        )
        assert device.status_code == 201, device.text
        device_id = device.json()["id"]

        profile = client.post(
            "/api/v1/analyzer-transport/profiles",
            headers=headers,
            json={
                "device_id": device_id,
                "frame_payload_size": 64,
                "ack_timeout_seconds": 10,
                "max_retries": 1,
            },
        )
        assert profile.status_code == 201, profile.text

        transport_session = client.post(
            "/api/v1/analyzer-transport/sessions",
            headers=headers,
            json={"device_id": device_id},
        )
        assert transport_session.status_code == 201, transport_session.text
        session_id = transport_session.json()["id"]

        queued = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/queue-outbound",
            headers=headers,
            json={
                "message_type": "ASTM-WORKLIST",
                "logical_payload": r"H|\^&|||ASTM-TX-DLQ-01|||||P|1\rL|1|N\r",
            },
        )
        assert queued.status_code == 201, queued.text
        message_id = queued.json()["id"]

        assert client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/next",
            headers=headers,
        ).status_code == 200
        assert client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/ack",
            headers=headers,
        ).status_code == 200

        first_frame = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/next",
            headers=headers,
        )
        assert first_frame.status_code == 200, first_frame.text
        assert first_frame.json()["transport_item"]["kind"] == "frame"

        first_nak = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/nak",
            headers=headers,
        )
        assert first_nak.status_code == 200, first_nak.text
        assert first_nak.json()["decision"] == "resend"

        resend = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/next",
            headers=headers,
        )
        assert resend.status_code == 200, resend.text
        assert resend.json()["transport_item"]["kind"] == "frame"

        second_nak = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/nak",
            headers=headers,
        )
        assert second_nak.status_code == 200, second_nak.text
        assert second_nak.json()["decision"] == "failed"
        assert second_nak.json()["message"]["transport_status"] == "failed"
        assert second_nak.json()["session"]["session_status"] == "error"

        dead_letter = client.post(
            f"/api/v1/analyzer-transport/messages/{message_id}/dead-letter",
            headers=headers,
            json={"notes": "operator-dead-letter"},
        )
        assert dead_letter.status_code == 200, dead_letter.text
        assert dead_letter.json()["message"]["transport_status"] == "dead_letter"
        assert dead_letter.json()["session"]["session_status"] == "idle"

        requeue = client.post(
            f"/api/v1/analyzer-transport/messages/{message_id}/requeue",
            headers=headers,
            json={"notes": "operator-requeue"},
        )
        assert requeue.status_code == 200, requeue.text
        assert requeue.json()["message"]["transport_status"] == "queued"
        assert requeue.json()["message"]["retry_count"] == 0
        assert requeue.json()["message"]["next_frame_index"] == 0
        assert requeue.json()["session"]["session_status"] == "sending"


def test_analyzer_transport_runtime_metrics_include_dead_letter(tmp_path):
    with make_client(tmp_path, "lis-transport-metrics.sqlite3") as client:
        headers, _ = bootstrap_admin(client)

        device = client.post(
            "/api/v1/devices",
            headers=headers,
            json={
                "code": "ASTM-TX-METRICS-01",
                "display_name": "Transport metrics analyzer",
                "protocol": "astm",
            },
        )
        assert device.status_code == 201, device.text
        device_id = device.json()["id"]

        profile = client.post(
            "/api/v1/analyzer-transport/profiles",
            headers=headers,
            json={
                "device_id": device_id,
                "frame_payload_size": 64,
                "ack_timeout_seconds": 10,
                "max_retries": 0,
            },
        )
        assert profile.status_code == 201, profile.text

        transport_session = client.post(
            "/api/v1/analyzer-transport/sessions",
            headers=headers,
            json={"device_id": device_id},
        )
        assert transport_session.status_code == 201, transport_session.text
        session_id = transport_session.json()["id"]

        queued = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/queue-outbound",
            headers=headers,
            json={
                "message_type": "ASTM-WORKLIST",
                "logical_payload": r"H|\^&|||ASTM-TX-METRICS-01|||||P|1\rL|1|N\r",
            },
        )
        assert queued.status_code == 201, queued.text
        message_id = queued.json()["id"]

        assert client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/next",
            headers=headers,
        ).status_code == 200
        assert client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/ack",
            headers=headers,
        ).status_code == 200
        assert client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/next",
            headers=headers,
        ).status_code == 200

        failed = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/nak",
            headers=headers,
        )
        assert failed.status_code == 200, failed.text
        assert failed.json()["decision"] == "failed"

        dead_letter = client.post(
            f"/api/v1/analyzer-transport/messages/{message_id}/dead-letter",
            headers=headers,
            json={"notes": "metrics-dead-letter"},
        )
        assert dead_letter.status_code == 200, dead_letter.text

        metrics = client.get(
            "/api/v1/analyzer-transport/runtime/metrics",
            headers=headers,
            params={"device_id": device_id},
        )
        assert metrics.status_code == 200, metrics.text
        payload = metrics.json()
        assert payload["profile_count"] == 1
        assert payload["session_count"] == 1
        assert payload["message_count"] == 1
        assert payload["dead_letter_count"] == 1
        assert payload["failed_message_count"] == 0
        assert payload["status_counts"]["dead_letter"] == 1
