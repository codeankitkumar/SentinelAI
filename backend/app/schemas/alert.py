"""Alert schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int | None
    title: str
    description: str
    rule_name: str
    severity: str
    status: str
    score: float
    source_ip: str | None
    dst_ip: str | None
    protocol: str | None
    timestamp: datetime


class AlertUpdate(BaseModel):
    status: str | None = None
    severity: str | None = None


class AlertList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AlertOut]