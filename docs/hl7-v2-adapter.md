# HL7 v2 Adapter

The current LIS repo includes a starter HL7 v2 adapter focused on practical laboratory order
and result exchange.

Implemented interactions:

- `POST /api/v1/integrations/hl7v2/import/oml-o33`
- `POST /api/v1/integrations/hl7v2/import/oru-r01`
- `GET /api/v1/integrations/hl7v2/export/oml-o33/{order_id}`
- `GET /api/v1/integrations/hl7v2/export/oru-r01/{report_id}`
- `GET /api/v1/integrations/messages`

Supported message structures in the current starter:

- inbound `OML^O33` and compatible `ORM^O01` order-style imports,
- outbound `OML^O33` order export,
- inbound `ORU^R01` result import,
- outbound `ORU^R01` report/result export.

Current mapping decisions:

- `MSH` supplies message identity, source system, and control ID
- `PID` resolves or creates `patient_runtime`
- `ORC/OBR` map to `lis_order_runtime` and `lis_order_item_runtime`
- `SPM` maps to `specimen_runtime`
- `OBX` maps to `observation_runtime`
- all processed and failed messages are written to `interface_message_log_runtime`

Current limits:

- no ACK/NAK workflow,
- no retry queue or dead-letter handling,
- no `Z`-segment processing,
- no profile validation for site-specific implementation guides,
- no low-level ASTM / serial / TCP instrument transport.

This is intentionally a starter interoperability slice: enough to prove data flow and
message traceability without pretending to be a full production interface engine.
