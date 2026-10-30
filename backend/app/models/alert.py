"""Alert model representing a detected suspicious activity."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class AlertStatus:
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("network_events.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(2000), default="")
    rule_name: Mapped[str] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(
        String(16), default="low", index=True
    )
    status: Mapped[str] = mapped_column(
        String(16), default=AlertStatus.OPEN, index=True
    )
    score: Mapped[float] = mapped_column(Float, default=0.0)
    source_ip: Mapped[str | None] = mapped_column(String(45), index=True)
    dst_ip: Mapped[str | None] = mapped_column(String(45), index=True)
    protocol: Mapped[str | None] = mapped_column(String(16))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    event = relationship("NetworkEvent")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Alert {self.id} {self.rule_name} {self.severity} {self.status}>"