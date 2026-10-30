"""Incident schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IncidentNoteCreate(BaseModel):
    content: str = Field(min_length=1)


class IncidentNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    author_id: int | None
    author_name: str
    content: str
    created_at: datetime


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = ""
    severity: str = "medium"
    alert_ids: list[int] = Field(default_factory=list)


class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: str | None = None
    status: str | None = None
    assignee: str | None = None
    alert_ids: list[int] | None = None


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    severity: str
    status: str
    assignee: str | None
    created_at: datetime
    updated_at: datetime
    alert_count: int = 0


class IncidentDetail(IncidentOut):
    model_config = ConfigDict(from_attributes=True)

    notes: list[IncidentNoteOut] = Field(default_factory=list)