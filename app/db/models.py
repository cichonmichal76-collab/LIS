from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class UserRecord(Base):
    __tablename__ = "app_user_runtime"
    __table_args__ = (
        Index("ix_app_user_runtime_username", "username"),
        Index("ix_app_user_runtime_role_active", "role_code", "active"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(128))
    role_code: Mapped[str] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class DeviceRecord(Base):
    __tablename__ = "device_runtime"
    __table_args__ = (
        Index("ix_device_runtime_code", "code"),
        Index("ix_device_runtime_protocol_active", "protocol_code", "active"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    serial_no: Mapped[str | None] = mapped_column(String(128), nullable=True)
    protocol_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class PatientRecord(Base):
    __tablename__ = "patient_runtime"
    __table_args__ = (
        Index("ix_patient_runtime_mrn", "mrn"),
        Index("ix_patient_runtime_family_name", "family_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    mrn: Mapped[str] = mapped_column(String(64), unique=True)
    given_name: Mapped[str] = mapped_column(String(128))
    family_name: Mapped[str] = mapped_column(String(128))
    sex_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class TestCatalogRecord(Base):
    __tablename__ = "test_catalog_runtime"
    __table_args__ = (
        Index("ix_test_catalog_runtime_local_code", "local_code"),
        Index("ix_test_catalog_runtime_loinc", "loinc_num"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    local_code: Mapped[str] = mapped_column(String(64), unique=True)
    display_name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(32))
    loinc_num: Mapped[str | None] = mapped_column(String(64), nullable=True)
    specimen_type_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    default_ucum: Mapped[str | None] = mapped_column(String(32), nullable=True)
    result_value_type: Mapped[str] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class DeviceTestMapRecord(Base):
    __tablename__ = "device_test_map_runtime"
    __table_args__ = (
        Index("ix_device_test_map_runtime_device_code", "device_id", "incoming_test_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("device_runtime.id"))
    incoming_test_code: Mapped[str] = mapped_column(String(128))
    test_catalog_id: Mapped[str] = mapped_column(ForeignKey("test_catalog_runtime.id"))
    default_unit_ucum: Mapped[str | None] = mapped_column(String(32), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class OrderRecord(Base):
    __tablename__ = "lis_order_runtime"
    __table_args__ = (
        Index("ix_lis_order_runtime_patient_status", "patient_id", "status"),
        Index("ix_lis_order_runtime_requisition", "requisition_no"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    requisition_no: Mapped[str] = mapped_column(String(64), unique=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_runtime.id"), index=True)
    encounter_case_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_system: Mapped[str] = mapped_column(String(64))
    placer_order_no: Mapped[str | None] = mapped_column(String(128), nullable=True)
    priority: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(32))
    clinical_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_by_practitioner_role_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    order_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    items: Mapped[list["OrderItemRecord"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItemRecord.line_no",
    )
    specimens: Mapped[list["SpecimenRecord"]] = relationship(back_populates="order")


class OrderItemRecord(Base):
    __tablename__ = "lis_order_item_runtime"
    __table_args__ = (
        Index("ix_lis_order_item_runtime_order_status", "order_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("lis_order_runtime.id"))
    line_no: Mapped[int]
    test_catalog_id: Mapped[str] = mapped_column(ForeignKey("test_catalog_runtime.id"))
    requested_specimen_type_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    priority: Mapped[str | None] = mapped_column(String(24), nullable=True)
    reflex_policy_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    aoe_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    order: Mapped[OrderRecord] = relationship(back_populates="items")
    observations: Mapped[list["ObservationRecord"]] = relationship(back_populates="order_item")


class SpecimenRecord(Base):
    __tablename__ = "specimen_runtime"
    __table_args__ = (
        Index("ix_specimen_runtime_order_status", "order_id", "status"),
        Index("ix_specimen_runtime_accession", "accession_no"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    accession_no: Mapped[str] = mapped_column(String(64), unique=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("lis_order_runtime.id"))
    parent_specimen_id: Mapped[str | None] = mapped_column(
        ForeignKey("specimen_runtime.id"),
        nullable=True,
    )
    patient_id: Mapped[str] = mapped_column(String(36), index=True)
    specimen_type_code: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_by_practitioner_role_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_location_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    storage_location_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    position_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    specimen_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    order: Mapped[OrderRecord] = relationship(back_populates="specimens")
    containers: Mapped[list["ContainerRecord"]] = relationship(
        back_populates="specimen",
        cascade="all, delete-orphan",
        order_by="ContainerRecord.created_at",
    )
    events: Mapped[list["SpecimenEventRecord"]] = relationship(
        back_populates="specimen",
        cascade="all, delete-orphan",
        order_by="SpecimenEventRecord.occurred_at",
    )
    observations: Mapped[list["ObservationRecord"]] = relationship(back_populates="specimen")


class ContainerRecord(Base):
    __tablename__ = "container_runtime"
    __table_args__ = (
        Index("ix_container_runtime_specimen", "specimen_id", "created_at"),
        Index("ix_container_runtime_barcode", "barcode"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    specimen_id: Mapped[str] = mapped_column(ForeignKey("specimen_runtime.id"))
    parent_container_id: Mapped[str | None] = mapped_column(
        ForeignKey("container_runtime.id"),
        nullable=True,
    )
    barcode: Mapped[str] = mapped_column(String(128), unique=True)
    container_type_code: Mapped[str] = mapped_column(String(64))
    position_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    volume_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_ucum: Mapped[str | None] = mapped_column(String(32), nullable=True)
    storage_location_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="labeled")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    specimen: Mapped[SpecimenRecord] = relationship(back_populates="containers")


class SpecimenEventRecord(Base):
    __tablename__ = "specimen_event_runtime"
    __table_args__ = (
        Index("ix_specimen_event_runtime_specimen", "specimen_id", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    specimen_id: Mapped[str] = mapped_column(ForeignKey("specimen_runtime.id"))
    event_type: Mapped[str] = mapped_column(String(64))
    performed_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    location_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    specimen: Mapped[SpecimenRecord] = relationship(back_populates="events")


class TaskRecord(Base):
    __tablename__ = "task_work_runtime"
    __table_args__ = (
        Index("ix_task_work_runtime_queue_status", "queue_code", "status"),
        Index("ix_task_work_runtime_owner_status", "owner_user_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    group_identifier: Mapped[str | None] = mapped_column(String(128), nullable=True)
    based_on_order_item_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    focus_type: Mapped[str] = mapped_column(String(32))
    focus_id: Mapped[str] = mapped_column(String(36))
    queue_code: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    business_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(24), nullable=True)
    owner_user_id: Mapped[str | None] = mapped_column(ForeignKey("app_user_runtime.id"), nullable=True)
    owner_practitioner_role_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    authored_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    inputs_payload: Mapped[dict[str, Any]] = mapped_column("inputs", JSON, default=dict)
    outputs_payload: Mapped[dict[str, Any]] = mapped_column("outputs", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class RawInstrumentMessageRecord(Base):
    __tablename__ = "raw_instrument_message_runtime"
    __table_args__ = (
        Index("ix_raw_instrument_message_runtime_device_created", "device_id", "created_at"),
        Index("ix_raw_instrument_message_runtime_accession", "accession_no"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("device_runtime.id"))
    protocol: Mapped[str] = mapped_column(String(64))
    direction: Mapped[str] = mapped_column(String(16))
    message_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    accession_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    specimen_barcode: Mapped[str | None] = mapped_column(String(128), nullable=True)
    parser_version: Mapped[str] = mapped_column(String(64))
    payload: Mapped[str] = mapped_column(Text)
    parsed_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_observation_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ObservationRecord(Base):
    __tablename__ = "observation_runtime"
    __table_args__ = (
        Index("ix_observation_runtime_order_item_status", "order_item_id", "status"),
        Index("ix_observation_runtime_specimen", "specimen_id"),
        Index("ix_observation_runtime_code_loinc", "code_loinc"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_item_id: Mapped[str] = mapped_column(ForeignKey("lis_order_item_runtime.id"))
    specimen_id: Mapped[str | None] = mapped_column(ForeignKey("specimen_runtime.id"), nullable=True)
    code_local: Mapped[str] = mapped_column(String(128))
    code_loinc: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    category_code: Mapped[str] = mapped_column(String(32), default="laboratory")
    value_type: Mapped[str] = mapped_column(String(32))
    value_num: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    value_code_system: Mapped[str | None] = mapped_column(String(128), nullable=True)
    value_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    unit_ucum: Mapped[str | None] = mapped_column(String(32), nullable=True)
    interpretation_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    abnormal_flag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    method_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    raw_message_id: Mapped[str | None] = mapped_column(
        ForeignKey("raw_instrument_message_runtime.id"),
        nullable=True,
    )
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reference_interval_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    order_item: Mapped[OrderItemRecord] = relationship(back_populates="observations")
    specimen: Mapped[SpecimenRecord | None] = relationship(back_populates="observations")
    report_observations: Mapped[list["ReportObservationRecord"]] = relationship(back_populates="observation")


class AutoverificationRuleRecord(Base):
    __tablename__ = "autoverification_rule_runtime"
    __table_args__ = (
        Index(
            "ix_autoverification_rule_runtime_scope",
            "test_catalog_id",
            "device_id",
            "specimen_type_code",
            "active",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(default=100)
    test_catalog_id: Mapped[str | None] = mapped_column(
        ForeignKey("test_catalog_runtime.id"),
        nullable=True,
    )
    device_id: Mapped[str | None] = mapped_column(ForeignKey("device_runtime.id"), nullable=True)
    specimen_type_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(32), default="basic")
    condition_payload: Mapped[dict[str, Any]] = mapped_column("condition_json", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AutoverificationRunRecord(Base):
    __tablename__ = "autoverification_run_runtime"
    __table_args__ = (
        Index("ix_autoverification_run_runtime_observation", "observation_id", "evaluated_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    observation_id: Mapped[str] = mapped_column(ForeignKey("observation_runtime.id"))
    rule_id: Mapped[str | None] = mapped_column(
        ForeignKey("autoverification_rule_runtime.id"),
        nullable=True,
    )
    decision: Mapped[str] = mapped_column(String(32))
    reasons_payload: Mapped[list[str]] = mapped_column("reasons_json", JSON, default=list)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_task_id: Mapped[str | None] = mapped_column(
        ForeignKey("task_work_runtime.id"),
        nullable=True,
    )


class ObservationLinkRecord(Base):
    __tablename__ = "observation_link_runtime"
    __table_args__ = (
        Index("ix_observation_link_runtime_source", "source_observation_id", "relation_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_observation_id: Mapped[str] = mapped_column(ForeignKey("observation_runtime.id"))
    target_observation_id: Mapped[str] = mapped_column(ForeignKey("observation_runtime.id"))
    relation_type: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DiagnosticReportRecord(Base):
    __tablename__ = "diagnostic_report_runtime"
    __table_args__ = (
        Index("ix_diagnostic_report_runtime_order_status", "order_id", "status"),
        Index("ix_diagnostic_report_runtime_patient", "patient_id", "issued_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_no: Mapped[str] = mapped_column(String(64), unique=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("lis_order_runtime.id"))
    patient_id: Mapped[str] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(32))
    category_code: Mapped[str] = mapped_column(String(32), default="laboratory")
    code_local: Mapped[str | None] = mapped_column(String(128), nullable=True)
    code_loinc: Mapped[str | None] = mapped_column(String(64), nullable=True)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    conclusion_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_version_no: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    versions: Mapped[list["DiagnosticReportVersionRecord"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="DiagnosticReportVersionRecord.version_no",
    )
    report_observations: Mapped[list["ReportObservationRecord"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ReportObservationRecord.sort_order",
    )


class DiagnosticReportVersionRecord(Base):
    __tablename__ = "diagnostic_report_version_runtime"
    __table_args__ = (
        Index("ix_diagnostic_report_version_runtime_report", "report_id", "version_no"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("diagnostic_report_runtime.id"))
    version_no: Mapped[int]
    status: Mapped[str] = mapped_column(String(32))
    amendment_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rendered_pdf_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("app_user_runtime.id"), nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    report: Mapped[DiagnosticReportRecord] = relationship(back_populates="versions")


class ReportObservationRecord(Base):
    __tablename__ = "report_observation_runtime"
    __table_args__ = (
        Index("ix_report_observation_runtime_report", "report_id", "sort_order"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("diagnostic_report_runtime.id"))
    observation_id: Mapped[str] = mapped_column(ForeignKey("observation_runtime.id"))
    sort_order: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    report: Mapped[DiagnosticReportRecord] = relationship(back_populates="report_observations")
    observation: Mapped[ObservationRecord] = relationship(back_populates="report_observations")


class InterfaceMessageLogRecord(Base):
    __tablename__ = "interface_message_log_runtime"
    __table_args__ = (
        Index("ix_interface_message_log_runtime_protocol_created", "protocol", "created_at"),
        Index("ix_interface_message_log_runtime_control_id", "control_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    protocol: Mapped[str] = mapped_column(String(32))
    direction: Mapped[str] = mapped_column(String(16))
    message_type: Mapped[str] = mapped_column(String(64))
    control_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    related_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[str] = mapped_column(Text)
    processed_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditEventRecord(Base):
    __tablename__ = "audit_event_log_runtime"
    __table_args__ = (
        Index("ix_audit_event_log_runtime_entity", "entity_type", "entity_id", "event_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    source_system: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ProvenanceRecord(Base):
    __tablename__ = "provenance_record_runtime"
    __table_args__ = (
        Index(
            "ix_provenance_record_runtime_target",
            "target_resource_type",
            "target_resource_id",
            "recorded_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    target_resource_type: Mapped[str] = mapped_column(String(64))
    target_resource_id: Mapped[str] = mapped_column(String(36))
    activity_code: Mapped[str] = mapped_column(String(64))
    based_on_order_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    based_on_order_item_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    specimen_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    observation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    report_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    agent_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    agent_practitioner_role_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    signature: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
