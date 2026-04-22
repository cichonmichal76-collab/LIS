# ASTM Driver Layer

The v6 slice adds a small ASTM-style driver layer for analyzer worklists and result ingest.

## What Is Implemented

- ASTM-style worklist export for a device
- ASTM-style result import for a device
- raw payload persistence in `raw_instrument_message`
- interface logging in `interface_message_log`
- `incoming_test_code -> test_catalog` mapping through `device_test_map`
- optional chaining into autoverification after import

## API Surface

- `GET /api/v1/integrations/astm/export/worklist/{device_id}`
- `POST /api/v1/integrations/astm/import/results`

## Minimal Supported Shape

Example result message:

```text
H|\^&|||ASTM-01|||||P|1
P|1||MRN-ASTM-1||Nowak^Anna
O|1|ACC-ASTM-1||GLU-ASTM^Glucose ASTM|R
R|1|GLU-ASTM^Glucose ASTM|99.4|mg/dL|N||F|20260422112900
L|1|N
```

The parser intentionally stays small and only supports the record types used in the starter workflow:

- `H`
- `P`
- `O`
- `R`
- `L`

## Design Intent

This is an ASTM-style adapter layer, not a complete implementation of every ASTM E1381 or E1394 transport and payload variant. It is meant to be a clean starting point for:

- device-specific parsers
- framing and ACK handling
- retry and dead-letter queue behavior
- separation of order download and result upload flows
