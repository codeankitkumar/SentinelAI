"""Network event model storing captured/analyzed flows.

Events are collected only from authorized traffic (See docs/SECURITY_LAB.md).
The `features_json` column stores the numeric feature vector used by the ML
model so inference results are reproducible.
"""
import json
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ThreatType:
    NORMAL = "normal"
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    DDOS = "ddos"
    ABNORMAL = "abnormal"


class NetworkEvent(Base):
    __tablename__ = "network_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    # Connection 5-tuple
    src_ip: Mapped[str] = mapped_column(String(45), index=True)
    dst_ip: Mapped[str] = mapped_column(String(45), index=True)
    protocol: Mapped[str] = mapped_column(String(16))
    src_port: Mapped[int] = mapped_column(Integer, default=0)
    dst_port: Mapped[int] = mapped_column(Integer, default=0)

    # Basic flow metrics
    bytes_sent: Mapped[float] = mapped_column(Float, default=0.0)
    bytes_recv: Mapped[float] = mapped_column(Float, default=0.0)
    packet_count: Mapped[int] = mapped_column(Integer, default=0)
    duration: Mapped[float] = mapped_column(Float, default=0.0)

    # ML-derived fields
    features_json: Mapped[str] = mapped_column(JSON, default=dict)
    threat_type: Mapped[str] = mapped_column(String(32), default=ThreatType.NORMAL, index=True)
    threat_score: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(16), default="info", index=True)
    rule_hits: Mapped[list] = mapped_column(JSON, default=list)

    def feature_dict(self) -> dict:
        if isinstance(self.features_json, str):
            try:
                return json.loads(self.features_json)
            except (TypeError, ValueError):
                return {}
        return dict(self.features_json or {})


__table_args__ = (Index("ix_events_time_threat", "timestamp", "threat_type"),)
NetworkEvent.__table_args__ = __table_args__