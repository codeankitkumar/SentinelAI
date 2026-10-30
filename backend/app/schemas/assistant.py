"""AI assistant schemas."""
from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    intent: str = Field(
        description="Type of request: explain | summarize | investigate | remediate | report"
    )
    query: str = Field(default="", max_length=3000)
    alert_id: int | None = None
    incident_id: int | None = None
    source_ip: str | None = None


class AssistantResponse(BaseModel):
    intent: str
    answer: str
    sources: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)