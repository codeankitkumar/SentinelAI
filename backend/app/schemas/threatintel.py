"""Threat intelligence schema."""
from pydantic import BaseModel, Field


class ThreatIntelResult(BaseModel):
    ip: str
    provider: str
    found: bool
    data: dict = Field(default_factory=dict)
    note: str = ""
    queried_at: str = ""