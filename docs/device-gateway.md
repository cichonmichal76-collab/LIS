# Device Gateway

The current LIS repo includes a starter device gateway that separates analyzer-facing ingest
from the transactional LIS core.

Implemented interactions:

- `POST /api/v1/devices`
- `GET /api/v1/devices`
- `GET /api/v1/devices/{device_id}`
- `POST /api/v1/devices/{device_id}/mappings`
- `GET /api/v1/devices/{device_id}/mappings`
- `GET /api/v1/integrations/device-gateway/worklists/{device_id}`
- `POST /api/v1/integrations/device-gateway/ingest`
- `GET /api/v1/integrations/device-gateway/messages`

Current runtime responsibilities:

- device registry with logical code, protocol, manufacturer, and model
- mapping `incoming_test_code -> test_catalog`
- device worklist generation from active mappings and pending order items
- analyzer result ingest into `observation_runtime`
- raw payload traceability through `raw_instrument_message_runtime`

Current traceability path:

`device_runtime -> raw_instrument_message_runtime -> observation_runtime -> diagnostic_report_runtime`

The gateway also writes:

- `audit_event_log_runtime`
- `provenance_record_runtime`

Current limits:

- no vendor-specific drivers,
- no ASTM / CLSI low-level transport stack,
- no ACK/NAK queueing,
- no parser plugins per instrument family,
- no autoverification or QC engine yet.

This slice is meant to be the extension point for real analyzer connectors, not the final
device integration product.
