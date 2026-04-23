from __future__ import annotations

from datetime import UTC, datetime
import os

from app.services.analyzer_transport import frame_astm_message
from _smoke_support import make_smoke_client


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    os.environ.pop("LIS_DATABASE_URL", None)

    with make_smoke_client("smoke_test_transport") as client:
        bootstrap = client.post(
            "/api/v1/auth/bootstrap-admin",
            json={
                "username": "admin",
                "password": "admin12345",
                "display_name": "Admin",
            },
        )
        assert bootstrap.status_code == 201, bootstrap.text
        headers = auth_headers(bootstrap.json()["access_token"])

        patient = client.post(
            "/api/v1/patients",
            headers=headers,
            json={
                "mrn": "MRN-SMOKE-TX-1",
                "given_name": "Anna",
                "family_name": "Smoke",
                "sex_code": "F",
            },
        )
        assert patient.status_code == 201, patient.text
        patient_id = patient.json()["id"]

        catalog = client.post(
            "/api/v1/test-catalog",
            headers=headers,
            json={
                "local_code": "GLU-SMOKE-TX",
                "display_name": "Glucose smoke transport",
                "kind": "orderable",
                "loinc_num": "2345-7",
                "specimen_type_code": "SER",
                "default_ucum": "mg/dL",
                "result_value_type": "quantity",
            },
        )
        assert catalog.status_code == 201, catalog.text
        catalog_id = catalog.json()["id"]

        order = client.post(
            "/api/v1/orders",
            headers=headers,
            json={
                "patient_id": patient_id,
                "source_system": "smoke",
                "priority": "routine",
                "ordered_at": datetime.now(UTC).isoformat(),
                "items": [{"test_catalog_id": catalog_id, "requested_specimen_type_code": "SER"}],
            },
        )
        assert order.status_code == 201, order.text
        order_id = order.json()["id"]
        order_detail = client.get(f"/api/v1/orders/{order_id}", headers=headers)
        assert order_detail.status_code == 200, order_detail.text
        order_item_id = order_detail.json()["items"][0]["id"]

        specimen = client.post(
            "/api/v1/specimens/accession",
            headers=headers,
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
            headers=headers,
            json={
                "collected_at": datetime.now(UTC).isoformat(),
                "container_barcodes": ["TUBE-SMOKE-TX-001"],
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

        device = client.post(
            "/api/v1/devices",
            headers=headers,
            json={
                "code": "ASTM-SMOKE-TX",
                "display_name": "Transport smoke analyzer",
                "protocol": "astm",
            },
        )
        assert device.status_code == 201, device.text
        device_id = device.json()["id"]

        mapping = client.post(
            f"/api/v1/devices/{device_id}/mappings",
            headers=headers,
            json={
                "incoming_test_code": "GLU-SMOKE-TX",
                "test_catalog_id": catalog_id,
                "default_unit_ucum": "mg/dL",
            },
        )
        assert mapping.status_code == 201, mapping.text

        profile = client.post(
            "/api/v1/analyzer-transport/profiles",
            headers=headers,
            json={
                "device_id": device_id,
                "frame_payload_size": 256,
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
            f"/api/v1/analyzer-transport/sessions/{session_id}/queue-astm-worklist",
            headers=headers,
        )
        assert queued.status_code == 201, queued.text
        assert queued.json()["extra"]["worklist_items"] >= 1

        next_item = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/next",
            headers=headers,
        )
        assert next_item.status_code == 200, next_item.text
        assert next_item.json()["transport_item"]["control_code"] == "ENQ"
        assert client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/ack",
            headers=headers,
        ).status_code == 200

        frame_item = client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/next",
            headers=headers,
        )
        assert frame_item.status_code == 200, frame_item.text
        assert frame_item.json()["transport_item"]["kind"] == "frame"
        assert client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/ack",
            headers=headers,
        ).status_code == 200
        assert client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/next",
            headers=headers,
        ).json()["transport_item"]["control_code"] == "EOT"
        assert client.post(
            f"/api/v1/analyzer-transport/sessions/{session_id}/outbound/ack",
            headers=headers,
        ).status_code == 200

        inbound_session = client.post(
            "/api/v1/analyzer-transport/sessions",
            headers=headers,
            json={"device_id": device_id},
        )
        assert inbound_session.status_code == 201, inbound_session.text
        inbound_session_id = inbound_session.json()["id"]

        enq = client.post(
            f"/api/v1/analyzer-transport/sessions/{inbound_session_id}/inbound/control",
            headers=headers,
            json={"control_code": "ENQ"},
        )
        assert enq.status_code == 200, enq.text
        assert enq.json()["reply_control_code"] == "ACK"

        astm_message = "\r".join(
            [
                r"H|\^&|||ASTM-SMOKE-TX|||||P|1",
                "P|1||MRN-SMOKE-TX-1||Smoke^Anna",
                f"O|1|{accession_no}||GLU-SMOKE-TX^Glucose smoke transport|R",
                "R|1|GLU-SMOKE-TX^Glucose smoke transport|101.2|mg/dL|N||F|20260423090000",
                "L|1|N",
                "",
            ]
        )
        frame = frame_astm_message(astm_message, frame_payload_size=1000)[0]["framed_payload_escaped"]
        inbound = client.post(
            f"/api/v1/analyzer-transport/sessions/{inbound_session_id}/inbound/frame",
            headers=headers,
            json={
                "framed_payload": frame,
                "auto_dispatch_astm": True,
                "auto_verify": False,
            },
        )
        assert inbound.status_code == 200, inbound.text
        assert inbound.json()["accepted"] is True
        assert inbound.json()["assembled"] is True
        assert inbound.json()["dispatch"]["created_observations"][0]["order_item_id"] == order_item_id
        assert client.post(
            f"/api/v1/analyzer-transport/sessions/{inbound_session_id}/inbound/control",
            headers=headers,
            json={"control_code": "EOT"},
        ).status_code == 200

        print("Analyzer transport smoke OK")
        print(
            {
                "worklist_session_id": session_id,
                "inbound_session_id": inbound_session_id,
                "device_id": device_id,
            }
        )


if __name__ == "__main__":
    main()
