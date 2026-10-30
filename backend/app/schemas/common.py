"""Common/shared schemas."""
from datetime import datetime

from pydantic import BaseModel


class ApiMessage(BaseModel):
    message: str


class Pagination(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0


class Page(BaseModel):
    total: int
    page: int
    page_size: int
    items: list


class Severity(BaseModel):
    """Sentinel severity scale used by alerts & incidents."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    INFO = "info"


class TimeRange(BaseModel):
    start: datetime | None = None
    end: datetime | None = None