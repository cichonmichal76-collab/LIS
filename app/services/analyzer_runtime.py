from __future__ import annotations

import socket
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import (
    AnalyzerTransportMessageRecord,
    AnalyzerTransportProfileRecord,
    AnalyzerTransportSessionRecord,
)
from app.schemas.analyzer_transport import (
    AnalyzerTransportConnectionMode,
    AnalyzerTransportReceiveControlRequest,
    AnalyzerTransportReceiveFrameRequest,
    AnalyzerTransportSessionCreateRequest,
)
from app.services import analyzer_transport as transport_service


class AnalyzerConnector(Protocol):
    def open(self) -> None: ...

    def close(self) -> None: ...

    def is_open(self) -> bool: ...

    def read(self, *, timeout_seconds: float) -> str | None: ...

    def write(self, payload: str, *, timeout_seconds: float) -> None: ...

    def describe(self) -> str: ...


@dataclass(slots=True)
class AnalyzerRuntimeStats:
    profiles_seen: int = 0
    sessions_touched: int = 0
    outbound_sent: int = 0
    inbound_processed: int = 0
    replies_sent: int = 0
    dispatches: int = 0
    timeouts: int = 0
    errors: list[str] = field(default_factory=list)


class MockAnalyzerConnector:
    def __init__(self, *, label: str):
        self.label = label
        self._open = False
        self._inbound: deque[str] = deque()
        self.outbound_payloads: list[str] = []

    def open(self) -> None:
        self._open = True

    def close(self) -> None:
        self._open = False

    def is_open(self) -> bool:
        return self._open

    def read(self, *, timeout_seconds: float) -> str | None:
        if self._inbound:
            return self._inbound.popleft()
        if timeout_seconds > 0:
            time.sleep(timeout_seconds)
        return None

    def write(self, payload: str, *, timeout_seconds: float) -> None:
        self.outbound_payloads.append(payload)

    def enqueue_inbound(self, *payloads: str) -> None:
        self._inbound.extend(payloads)

    def describe(self) -> str:
        return f"mock:{self.label}"


class TCPAnalyzerConnector:
    def __init__(self, *, host: str, port: int):
        self.host = host
        self.port = port
        self._socket: socket.socket | None = None
        self._buffer = bytearray()

    def open(self) -> None:
        if self._socket is not None:
            return
        self._socket = socket.create_connection((self.host, self.port), timeout=5.0)

    def close(self) -> None:
        if self._socket is None:
            return
        try:
            self._socket.close()
        finally:
            self._socket = None
            self._buffer.clear()

    def is_open(self) -> bool:
        return self._socket is not None

    def read(self, *, timeout_seconds: float) -> str | None:
        self.open()
        assert self._socket is not None
        self._socket.settimeout(timeout_seconds)
        try:
            chunk = self._socket.recv(4096)
        except TimeoutError:
            return _extract_transport_item(self._buffer)
        except socket.timeout:
            return _extract_transport_item(self._buffer)
        if chunk:
            self._buffer.extend(chunk)
        return _extract_transport_item(self._buffer)

    def write(self, payload: str, *, timeout_seconds: float) -> None:
        self.open()
        assert self._socket is not None
        self._socket.settimeout(timeout_seconds)
        self._socket.sendall(payload.encode("ascii"))

    def describe(self) -> str:
        return f"tcp-client:{self.host}:{self.port}"


class SerialAnalyzerConnector:
    def __init__(self, *, port: str, baudrate: int):
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self._buffer = bytearray()

    def open(self) -> None:
        if self._serial is not None:
            return
        try:
            import serial  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "pyserial is not installed. Serial runtime requires the optional serial dependency."
            ) from exc
        self._serial = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=0)

    def close(self) -> None:
        if self._serial is None:
            return
        try:
            self._serial.close()
        finally:
            self._serial = None
            self._buffer.clear()

    def is_open(self) -> bool:
        return self._serial is not None

    def read(self, *, timeout_seconds: float) -> str | None:
        self.open()
        assert self._serial is not None
        self._serial.timeout = timeout_seconds
        chunk = self._serial.read(4096)
        if chunk:
            self._buffer.extend(chunk)
        return _extract_transport_item(self._buffer)

    def write(self, payload: str, *, timeout_seconds: float) -> None:
        self.open()
        assert self._serial is not None
        self._serial.write_timeout = timeout_seconds
        self._serial.write(payload.encode("ascii"))

    def describe(self) -> str:
        return f"serial:{self.port}@{self.baudrate}"


class AnalyzerRuntimeWorker:
    def __init__(self, session_factory):
        self._session_factory = session_factory
        self._connectors: dict[str, AnalyzerConnector] = {}

    def register_connector(self, profile_id: UUID | str, connector: AnalyzerConnector) -> None:
        self._connectors[str(profile_id)] = connector

    def get_mock_connector(self, profile_id: UUID | str) -> MockAnalyzerConnector:
        connector = self._connectors[str(profile_id)]
        if not isinstance(connector, MockAnalyzerConnector):
            raise TypeError(f"Connector for profile {profile_id} is not a mock connector.")
        return connector

    def run_once(
        self,
        *,
        device_id: UUID | None = None,
        profile_id: UUID | None = None,
        create_missing_sessions: bool = True,
    ) -> AnalyzerRuntimeStats:
        stats = AnalyzerRuntimeStats()
        for current_profile_id in self._active_profile_ids(device_id=device_id, profile_id=profile_id):
            stats.profiles_seen += 1
            try:
                with self._session_factory() as session:
                    profile = session.get(AnalyzerTransportProfileRecord, current_profile_id)
                    if profile is None or not profile.active:
                        continue
                    transport_session = self._ensure_runtime_session(
                        session,
                        profile,
                        create_missing=create_missing_sessions,
                    )
                    if transport_session is None:
                        continue
                    stats.sessions_touched += 1
                    connector = self._ensure_connector(profile)
                    if not connector.is_open():
                        connector.open()
                    self._drain_available_inbound(
                        session,
                        profile=profile,
                        transport_session=transport_session,
                        connector=connector,
                        stats=stats,
                    )
                    self._handle_ack_timeout(
                        session,
                        profile=profile,
                        transport_session=transport_session,
                        stats=stats,
                    )
                    self._send_next_outbound(
                        session,
                        profile=profile,
                        transport_session=transport_session,
                        connector=connector,
                        stats=stats,
                    )
            except Exception as exc:
                stats.errors.append(f"{current_profile_id}: {exc}")
                self._record_runtime_error(current_profile_id, str(exc))
        return stats

    def run_forever(
        self,
        *,
        sleep_seconds: float = 1.0,
        max_iterations: int | None = None,
        device_id: UUID | None = None,
        profile_id: UUID | None = None,
    ) -> None:
        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            self.run_once(device_id=device_id, profile_id=profile_id)
            iteration += 1
            time.sleep(sleep_seconds)

    def close(self) -> None:
        for connector in self._connectors.values():
            connector.close()
        self._connectors.clear()

    def _active_profile_ids(
        self,
        *,
        device_id: UUID | None = None,
        profile_id: UUID | None = None,
    ) -> list[str]:
        with self._session_factory() as session:
            stmt: Select[tuple[AnalyzerTransportProfileRecord]] = select(
                AnalyzerTransportProfileRecord.id
            ).where(AnalyzerTransportProfileRecord.active.is_(True))
            if device_id is not None:
                stmt = stmt.where(AnalyzerTransportProfileRecord.device_id == str(device_id))
            if profile_id is not None:
                stmt = stmt.where(AnalyzerTransportProfileRecord.id == str(profile_id))
            return list(session.scalars(stmt).all())

    def _ensure_runtime_session(
        self,
        session: Session,
        profile: AnalyzerTransportProfileRecord,
        *,
        create_missing: bool,
    ) -> AnalyzerTransportSessionRecord | None:
        existing = session.scalar(
            select(AnalyzerTransportSessionRecord)
            .where(
                AnalyzerTransportSessionRecord.profile_id == profile.id,
                AnalyzerTransportSessionRecord.session_status != "closed",
            )
            .order_by(AnalyzerTransportSessionRecord.last_activity_at.desc())
            .limit(1)
        )
        if existing is not None:
            return existing
        if not create_missing:
            return None
        created = transport_service.create_session(
            session,
            AnalyzerTransportSessionCreateRequest(
                device_id=UUID(profile.device_id),
                profile_id=UUID(profile.id),
            ),
            actor=None,
        )
        return session.get(AnalyzerTransportSessionRecord, str(created.id))

    def _ensure_connector(self, profile: AnalyzerTransportProfileRecord) -> AnalyzerConnector:
        existing = self._connectors.get(profile.id)
        if existing is not None:
            return existing

        mode = AnalyzerTransportConnectionMode(profile.connection_mode)
        if mode == AnalyzerTransportConnectionMode.MOCK:
            connector = MockAnalyzerConnector(label=profile.id)
        elif mode == AnalyzerTransportConnectionMode.TCP_CLIENT:
            if not profile.tcp_host or profile.tcp_port is None:
                raise RuntimeError(
                    f"Profile {profile.id} is missing tcp_host/tcp_port for tcp-client mode."
                )
            connector = TCPAnalyzerConnector(host=profile.tcp_host, port=profile.tcp_port)
        else:
            if not profile.serial_port:
                raise RuntimeError(
                    f"Profile {profile.id} is missing serial_port for serial mode."
                )
            connector = SerialAnalyzerConnector(
                port=profile.serial_port,
                baudrate=profile.serial_baudrate or 9600,
            )
        self._connectors[profile.id] = connector
        return connector

    def _drain_available_inbound(
        self,
        session: Session,
        *,
        profile: AnalyzerTransportProfileRecord,
        transport_session: AnalyzerTransportSessionRecord,
        connector: AnalyzerConnector,
        stats: AnalyzerRuntimeStats,
    ) -> None:
        for _ in range(16):
            inbound_payload = connector.read(timeout_seconds=0.0)
            if inbound_payload is None:
                break
            stats.inbound_processed += 1
            reply_payload = self._process_inbound_payload(
                session,
                profile=profile,
                transport_session=transport_session,
                inbound_payload=inbound_payload,
                stats=stats,
            )
            if reply_payload:
                connector.write(reply_payload, timeout_seconds=float(profile.write_timeout_seconds))
                stats.replies_sent += 1

    def _handle_ack_timeout(
        self,
        session: Session,
        *,
        profile: AnalyzerTransportProfileRecord,
        transport_session: AnalyzerTransportSessionRecord,
        stats: AnalyzerRuntimeStats,
    ) -> None:
        current_session = session.get(AnalyzerTransportSessionRecord, transport_session.id)
        if current_session is None or not current_session.outbound_message_id:
            return
        message = session.get(AnalyzerTransportMessageRecord, current_session.outbound_message_id)
        if message is None or message.transport_status != "awaiting_ack":
            return
        if message.ack_deadline_at is None or message.ack_deadline_at > datetime.now(UTC):
            return
        transport_service.timeout_outbound(
            session,
            session_id=UUID(current_session.id),
            actor=None,
            notes="runtime-timeout",
        )
        stats.timeouts += 1

    def _send_next_outbound(
        self,
        session: Session,
        *,
        profile: AnalyzerTransportProfileRecord,
        transport_session: AnalyzerTransportSessionRecord,
        connector: AnalyzerConnector,
        stats: AnalyzerRuntimeStats,
    ) -> None:
        response = transport_service.next_outbound_transport_item(
            session,
            session_id=UUID(transport_session.id),
        )
        if response.transport_item is None or response.awaiting_ack:
            return
        connector.write(
            response.transport_item.payload,
            timeout_seconds=float(profile.write_timeout_seconds),
        )
        stats.outbound_sent += 1

        if profile.read_timeout_seconds <= 0:
            return
        inbound_payload = connector.read(timeout_seconds=float(profile.read_timeout_seconds))
        if inbound_payload is None:
            return
        stats.inbound_processed += 1
        reply_payload = self._process_inbound_payload(
            session,
            profile=profile,
            transport_session=transport_session,
            inbound_payload=inbound_payload,
            stats=stats,
        )
        if reply_payload:
            connector.write(reply_payload, timeout_seconds=float(profile.write_timeout_seconds))
            stats.replies_sent += 1

    def _process_inbound_payload(
        self,
        session: Session,
        *,
        profile: AnalyzerTransportProfileRecord,
        transport_session: AnalyzerTransportSessionRecord,
        inbound_payload: str,
        stats: AnalyzerRuntimeStats,
    ) -> str | None:
        normalized = transport_service.normalize_transport_text(inbound_payload)
        if normalized in {
            transport_service.ENQ,
            transport_service.ACK,
            transport_service.NAK,
            transport_service.EOT,
        }:
            response = transport_service.receive_transport_control(
                session,
                session_id=UUID(transport_session.id),
                payload=AnalyzerTransportReceiveControlRequest(
                    control_code=transport_service.escape_transport_text(normalized)
                ),
                actor=None,
            )
            return response.reply_payload

        response = transport_service.receive_transport_frame(
            session,
            session_id=UUID(transport_session.id),
            payload=AnalyzerTransportReceiveFrameRequest(
                framed_payload=transport_service.escape_transport_text(normalized),
                auto_dispatch_astm=profile.auto_dispatch_astm,
                auto_verify=profile.auto_verify,
            ),
            actor=None,
        )
        if response.dispatch is not None:
            stats.dispatches += 1
        return response.reply_payload

    def _record_runtime_error(self, profile_id: str, error_text: str) -> None:
        with self._session_factory() as session:
            profile = session.get(AnalyzerTransportProfileRecord, profile_id)
            if profile is None:
                return
            current_session = session.scalar(
                select(AnalyzerTransportSessionRecord)
                .where(
                    AnalyzerTransportSessionRecord.profile_id == profile.id,
                    AnalyzerTransportSessionRecord.session_status != "closed",
                )
                .order_by(AnalyzerTransportSessionRecord.last_activity_at.desc())
                .limit(1)
            )
            if current_session is None:
                return
            current_session.session_status = "error"
            current_session.last_error = error_text
            current_session.last_activity_at = datetime.now(UTC)
            session.commit()


def _extract_transport_item(buffer: bytearray) -> str | None:
    if not buffer:
        return None

    while buffer and chr(buffer[0]) not in {
        transport_service.ENQ,
        transport_service.ACK,
        transport_service.NAK,
        transport_service.EOT,
        transport_service.STX,
    }:
        del buffer[0]

    if not buffer:
        return None

    first_char = chr(buffer[0])
    if first_char in {
        transport_service.ENQ,
        transport_service.ACK,
        transport_service.NAK,
        transport_service.EOT,
    }:
        del buffer[0]
        return first_char

    terminator = bytes(f"{transport_service.CR}{transport_service.LF}", "ascii")
    frame_end = buffer.find(terminator)
    if frame_end == -1:
        return None
    payload = bytes(buffer[: frame_end + len(terminator)])
    del buffer[: frame_end + len(terminator)]
    return payload.decode("ascii", errors="ignore")
