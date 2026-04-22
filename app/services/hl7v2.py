from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Iterable


@dataclass(slots=True)
class HL7Segment:
    name: str
    fields: list[str]

    def field(self, number: int) -> str:
        if number < len(self.fields):
            return self.fields[number]
        return ""

    def components(self, number: int) -> list[str]:
        value = self.field(number)
        return value.split("^") if value else []

    def first_component(self, number: int) -> str | None:
        for value in self.components(number):
            if value:
                return value
        return None


@dataclass(slots=True)
class HL7Message:
    raw: str
    field_sep: str
    encoding_chars: str
    segments: list[HL7Segment]

    def segment(self, name: str) -> HL7Segment | None:
        for segment in self.segments:
            if segment.name == name:
                return segment
        return None

    def message_type(self) -> str:
        msh = self.segment("MSH")
        return msh.field(9) if msh else ""

    def control_id(self) -> str:
        msh = self.segment("MSH")
        return msh.field(10) if msh else ""


def parse_hl7_message(raw_message: str) -> HL7Message:
    message = raw_message.replace("\n", "\r")
    lines = [line for line in message.split("\r") if line.strip()]
    if not lines or not lines[0].startswith("MSH"):
        raise ValueError("HL7 message must start with MSH segment")
    field_sep = lines[0][3]
    segments: list[HL7Segment] = []
    for line in lines:
        parts = line.split(field_sep)
        name = parts[0]
        if name == "MSH":
            normalized = ["MSH", field_sep] + parts[1:]
        else:
            normalized = parts
        segments.append(HL7Segment(name=name, fields=normalized))
    msh = next(segment for segment in segments if segment.name == "MSH")
    return HL7Message(
        raw=raw_message,
        field_sep=field_sep,
        encoding_chars=msh.field(2),
        segments=segments,
    )


def build_segment(name: str, fields: Iterable[str | int | float | None]) -> str:
    values = [name]
    for field in fields:
        values.append("" if field is None else str(field))
    return "|".join(values)


def join_segments(segments: Iterable[str]) -> str:
    return "\r".join(segments) + "\r"


def first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value is not None and str(value).strip():
            return str(value)
    return None


def code_parts(field_value: str | None) -> tuple[str | None, str | None, str | None]:
    if not field_value:
        return None, None, None
    parts = field_value.split("^")
    code = parts[0] if len(parts) > 0 and parts[0] else None
    text = parts[1] if len(parts) > 1 and parts[1] else None
    coding_system = parts[2] if len(parts) > 2 and parts[2] else None
    return code, text, coding_system


def hl7_ts_to_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    try:
        if len(trimmed) >= 14:
            return datetime.strptime(trimmed[:14], "%Y%m%d%H%M%S").replace(tzinfo=UTC)
        if len(trimmed) >= 12:
            return datetime.strptime(trimmed[:12], "%Y%m%d%H%M").replace(tzinfo=UTC)
        if len(trimmed) >= 8:
            return datetime.strptime(trimmed[:8], "%Y%m%d").replace(tzinfo=UTC)
    except ValueError:
        return None
    return None


def hl7_date_to_date(value: str | None) -> date | None:
    if not value:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    try:
        return datetime.strptime(trimmed[:8], "%Y%m%d").date()
    except ValueError:
        return None


def datetime_to_hl7_ts(value: datetime | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value.replace("-", "").replace(":", "").replace("T", "")[:14]
        value = parsed
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y%m%d%H%M%S")


def date_to_hl7_date(value: date | None) -> str:
    return value.strftime("%Y%m%d") if value else ""


def map_obx_status_to_internal(value: str | None) -> str:
    lookup = {
        "F": "final",
        "P": "preliminary",
        "C": "corrected",
        "W": "entered_in_error",
        "X": "cancelled",
        "I": "registered",
    }
    return lookup.get((value or "").strip().upper(), "registered")


def map_internal_observation_status_to_obx(value: str | None) -> str:
    lookup = {
        "final": "F",
        "preliminary": "P",
        "corrected": "C",
        "amended": "C",
        "cancelled": "X",
        "entered_in_error": "W",
        "registered": "I",
    }
    return lookup.get((value or "").strip().lower(), "F")


def map_report_status_to_obr(value: str | None) -> str:
    lookup = {
        "final": "F",
        "preliminary": "P",
        "corrected": "C",
        "amended": "C",
        "partial": "P",
        "registered": "I",
    }
    return lookup.get((value or "").strip().lower(), "F")
