"""Incident model for analyst-led investigations and report export."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class IncidentStatus:
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity:
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "info"


# Link incident <-> alert (many-to-many).
incident_alerts = Table(
    "incident_alerts",
    Base.metadata,
    Column("incident_id", ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True),
    Column("alert_id", ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True),
)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(
        String(16), default=IncidentSeverity.MEDIUM, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=IncidentStatus.OPEN, index=True
    )
    assignee: Mapped[str | None] = mapped_column(String(120))
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    assigned_user = relationship("User", foreign_keys=[assignee_id])
    alerts = relationship("Alert", secondary=incident_alerts, lazy="selectin")
    notes = relationship(
        "IncidentNote", back_populates="incident", cascade="all, delete-orphan"
    )