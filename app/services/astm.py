from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable


@dataclass(slots=True)
class ASTMRecord:
    record_type: str
    fields: list[str]

    def field(self, index: int) -> str:
        if index < len(self.fields):
            return self.fields[index]
        return ""


@dataclass(slots=True)
class ASTMOrder:
    sequence_no: str
    accession_no: str | None
    universal_test_id: str | None
    results: list[dict[str, str]]


@dataclass(slots=True)
class ASTMMessage:
    raw: str
    records: list[ASTMRecord]
    patient_id: str | None
    patient_name: str | None
    orders: list[ASTMOrder]


def _clean_line(line: str) -> str:
    return line.strip().lstrip("\x02").rstrip("\x03").strip()


def parse_astm_message(raw_message: str) -> ASTMMessage:
    normalized = raw_message.replace("\r", "\n")
    lines = [_clean_line(line) for line in normalized.split("\n") if _clean_line(line)]
    if not lines:
        raise ValueError("ASTM message is empty")

    records: list[ASTMRecord] = []
    orders: list[ASTMOrder] = []
    patient_id = None
    patient_name = None
    current_order: ASTMOrder | None = None

    for line in lines:
        parts = line.split("|")
        record_type = parts[0][:1]
        record = ASTMRecord(record_type=record_type, fields=parts)
        records.append(record)

        if record_type == "P":
            patient_id = parts[3] if len(parts) > 3 and parts[3] else patient_id
            patient_name = parts[5] if len(parts) > 5 and parts[5] else patient_name
        elif record_type == "O":
            current_order = ASTMOrder(
                sequence_no=parts[1] if len(parts) > 1 else "",
                accession_no=parts[2] if len(parts) > 2 and parts[2] else None,
                universal_test_id=parts[4] if len(parts) > 4 and parts[4] else None,
                results=[],
            )
            orders.append(current_order)
        elif record_type == "R":
            if current_order is None:
                raise ValueError("ASTM result record encountered before any order record")
            current_order.results.append(
                {
                    "sequence_no": parts[1] if len(parts) > 1 else "",
                    "test_id": parts[2] if len(parts) > 2 else "",
                    "value": parts[3] if len(parts) > 3 else "",
                    "unit": parts[4] if len(parts) > 4 else "",
                    "abnormal_flag": parts[5] if len(parts) > 5 else "",
                    "result_status": parts[7] if len(parts) > 7 else "",
                    "observed_at": parts[8] if len(parts) > 8 else "",
                }
            )
    return ASTMMessage(
        raw=raw_message,
        records=records,
        patient_id=patient_id,
        patient_name=patient_name,
        orders=orders,
    )


def astm_ts_to_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    try:
        if len(trimmed) >= 14:
            return datetime.strptime(trimmed[:14], "%Y%m%d%H%M%S").replace(tzinfo=UTC)
        if len(trimmed) >= 8:
            return datetime.strptime(trimmed[:8], "%Y%m%d").replace(tzinfo=UTC)
    except ValueError:
        return None
    return None


def build_astm_record(record_type: str, fields: Iterable[str | int | float | None]) -> str:
    values = [record_type]
    for field in fields:
        values.append("" if field is None else str(field))
    return "|".join(values)


def build_astm_worklist(device_code: str, items: list[dict[str, object]]) -> str:
    segments: list[str] = [
        build_astm_record("H", [r"\^&", "", "", device_code, "", "", "", "", "P", "1"]),
    ]
    for index, item in enumerate(items, start=1):
        segments.append(
            build_astm_record(
                "O",
                [
                    index,
                    item.get("accession_no"),
                    "",
                    f"{item.get('incoming_test_code')}^{item.get('display_name')}",
                    "R",
                ],
            )
        )
    segments.append(build_astm_record("L", ["1", "N"]))
    return "\r".join(segments) + "\r"
