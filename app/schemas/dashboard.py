from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import ApiModel


class DashboardMetric(ApiModel):
    key: str
    label: str
    value: int
    tone: str
    hint: str


class DashboardStatusSummary(ApiModel):
    label: str
    count: int


class DashboardQueueSummary(ApiModel):
    queue_code: str
    total: int
    ready: int
    in_progress: int
    completed: int


class DashboardActivityItem(ApiModel):
    id: str
    label: str
    secondary: str
    status: str
    timestamp: datetime


class DashboardOverviewResponse(ApiModel):
    service: str
    version: str
    database_backend: str
    database_status: str
    generated_at: datetime
    metrics: list[DashboardMetric] = Field(default_factory=list)
    order_statuses: list[DashboardStatusSummary] = Field(default_factory=list)
    specimen_statuses: list[DashboardStatusSummary] = Field(default_factory=list)
    task_statuses: list[DashboardStatusSummary] = Field(default_factory=list)
    task_queues: list[DashboardQueueSummary] = Field(default_factory=list)
    recent_orders: list[DashboardActivityItem] = Field(default_factory=list)
    recent_specimens: list[DashboardActivityItem] = Field(default_factory=list)
    recent_tasks: list[DashboardActivityItem] = Field(default_factory=list)
