"""Schemas for Admin Command Center analytics & KPI metrics."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class KPICardItem(BaseModel):
    label: str
    value: float
    formatted_value: str
    delta_percent: float | None = None
    trend: list[float]
    unit: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminMetricsResponse(BaseModel):
    total_ctxh: KPICardItem
    attendance_rate: KPICardItem
    active_users: KPICardItem
    monthly_growth: KPICardItem
    dau: int
    mau: int
    total_users: int
    total_activities: int
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)
