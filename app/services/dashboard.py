from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.config import APP_NAME, APP_VERSION, Settings
from app.db.models import (
    DeviceRecord,
    DiagnosticReportRecord,
    ObservationRecord,
    OrderRecord,
    PatientRecord,
    QcRunRecord,
    SpecimenRecord,
    TaskRecord,
)
from app.db.runtime import detect_database_backend
from app.schemas.dashboard import (
    DashboardActivityItem,
    DashboardMetric,
    DashboardOverviewResponse,
    DashboardQueueSummary,
    DashboardStatusSummary,
)


def build_overview(session: Session, settings: Settings) -> DashboardOverviewResponse:
    return DashboardOverviewResponse(
        service=APP_NAME,
        version=APP_VERSION,
        database_backend=detect_database_backend(settings.database_url),
        database_status="ok",
        generated_at=datetime.now(UTC),
        metrics=[
            DashboardMetric(
                key="patients",
                label="Patients",
                value=_count_rows(session, PatientRecord),
                tone="calm",
                hint="Registered patient records.",
            ),
            DashboardMetric(
                key="orders",
                label="Orders",
                value=_count_rows(session, OrderRecord),
                tone="brand",
                hint="Orders created across the current runtime store.",
            ),
            DashboardMetric(
                key="specimens",
                label="Specimens",
                value=_count_rows(session, SpecimenRecord),
                tone="accent",
                hint="Accessioned specimens ready for tracking.",
            ),
            DashboardMetric(
                key="open_tasks",
                label="Open Tasks",
                value=_count_open_tasks(session),
                tone="warning",
                hint="Everything not yet completed on the bench.",
            ),
            DashboardMetric(
                key="observations",
                label="Observations",
                value=_count_rows(session, ObservationRecord),
                tone="calm",
                hint="Generated or manually entered lab observations.",
            ),
            DashboardMetric(
                key="reports",
                label="Reports",
                value=_count_rows(session, DiagnosticReportRecord),
                tone="brand",
                hint="Diagnostic reports currently stored by the LIS.",
            ),
            DashboardMetric(
                key="devices",
                label="Devices",
                value=_count_rows(session, DeviceRecord),
                tone="accent",
                hint="Instrument and gateway registrations.",
            ),
            DashboardMetric(
                key="qc_runs",
                label="QC Runs",
                value=_count_rows(session, QcRunRecord),
                tone="warning",
                hint="Quality control runs logged for review.",
            ),
        ],
        order_statuses=_status_summary(session, OrderRecord.status),
        specimen_statuses=_status_summary(session, SpecimenRecord.status),
        task_statuses=_status_summary(session, TaskRecord.status),
        task_queues=_task_queue_summary(session),
        recent_orders=_recent_orders(session),
        recent_specimens=_recent_specimens(session),
        recent_tasks=_recent_tasks(session),
    )


def _count_rows(session: Session, model: type[object]) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


def _count_open_tasks(session: Session) -> int:
    return int(
        session.scalar(
            select(func.count()).select_from(TaskRecord).where(TaskRecord.status != "completed")
        )
        or 0
    )


def _status_summary(session: Session, status_column) -> list[DashboardStatusSummary]:
    rows = session.execute(
        select(status_column.label("label"), func.count().label("count"))
        .group_by(status_column)
        .order_by(func.count().desc(), status_column.asc())
        .limit(6)
    ).all()
    return [
        DashboardStatusSummary(label=str(row.label), count=int(row.count))
        for row in rows
        if row.label is not None
    ]


def _task_queue_summary(session: Session) -> list[DashboardQueueSummary]:
    ready = func.sum(case((TaskRecord.status == "ready", 1), else_=0))
    in_progress = func.sum(case((TaskRecord.status == "in_progress", 1), else_=0))
    completed = func.sum(case((TaskRecord.status == "completed", 1), else_=0))
    rows = session.execute(
        select(
            TaskRecord.queue_code,
            func.count().label("total"),
            ready.label("ready"),
            in_progress.label("in_progress"),
            completed.label("completed"),
        )
        .group_by(TaskRecord.queue_code)
        .order_by(func.count().desc(), TaskRecord.queue_code.asc())
        .limit(6)
    ).all()
    return [
        DashboardQueueSummary(
            queue_code=row.queue_code,
            total=int(row.total or 0),
            ready=int(row.ready or 0),
            in_progress=int(row.in_progress or 0),
            completed=int(row.completed or 0),
        )
        for row in rows
        if row.queue_code
    ]


def _recent_orders(session: Session) -> list[DashboardActivityItem]:
    rows = session.execute(
        select(
            OrderRecord.id,
            OrderRecord.requisition_no,
            OrderRecord.priority,
            OrderRecord.status,
            OrderRecord.ordered_at,
            OrderRecord.source_system,
        )
        .order_by(OrderRecord.created_at.desc())
        .limit(5)
    ).all()
    return [
        DashboardActivityItem(
            id=row.id,
            label=row.requisition_no,
            secondary=f"{row.priority.upper()} / {row.source_system}",
            status=row.status,
            timestamp=row.ordered_at,
        )
        for row in rows
    ]


def _recent_specimens(session: Session) -> list[DashboardActivityItem]:
    rows = session.execute(
        select(
            SpecimenRecord.id,
            SpecimenRecord.accession_no,
            SpecimenRecord.specimen_type_code,
            SpecimenRecord.status,
            SpecimenRecord.created_at,
        )
        .order_by(SpecimenRecord.created_at.desc())
        .limit(5)
    ).all()
    return [
        DashboardActivityItem(
            id=row.id,
            label=row.accession_no,
            secondary=f"{row.specimen_type_code} specimen",
            status=row.status,
            timestamp=row.created_at,
        )
        for row in rows
    ]


def _recent_tasks(session: Session) -> list[DashboardActivityItem]:
    rows = session.execute(
        select(
            TaskRecord.id,
            TaskRecord.queue_code,
            TaskRecord.focus_type,
            TaskRecord.status,
            TaskRecord.authored_on,
        )
        .order_by(TaskRecord.created_at.desc())
        .limit(5)
    ).all()
    return [
        DashboardActivityItem(
            id=row.id,
            label=row.queue_code,
            secondary=f"{row.focus_type} workflow",
            status=row.status,
            timestamp=row.authored_on,
        )
        for row in rows
    ]
