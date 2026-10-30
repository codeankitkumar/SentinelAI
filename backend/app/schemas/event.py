"""Network event schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NetworkEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    src_ip: str
    dst_ip: str
    protocol: str
    src_port: int
    dst_port: int
    bytes_sent: float
    bytes_recv: float
    packet_count: int
    duration: float
    threat_type: str
    threat_score: float
    severity: str
    rule_hits: list = Field(default_factory=list)


class NetworkEventFilter(BaseModel):
    query: str | None = None
    threat_type: str | None = None
    severity: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    page: int = 1
    page_size: int = 20