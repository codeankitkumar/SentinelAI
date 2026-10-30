"""Dashboard aggregation schemas."""
from pydantic import BaseModel


class StatCard(BaseModel):
    label: str
    value: int
    unit: str = ""


class AttackDistItem(BaseModel):
    threat_type: str
    count: int


class SeverityDistItem(BaseModel):
    severity: str
    count: int


class TrafficPoint(BaseModel):
    bucket: str
    events: int
    alerts: int


class TopIp(BaseModel):
    ip: str
    count: int
    severity: str


class RecentItem(BaseModel):
    id: int
    title: str
    severity: str
    status: str
    source_ip: str | None
    timestamp: object | None
    rule_name: str | None = None


class DashboardStats(BaseModel):
    total_events: int
    total_alerts: int
    critical_incidents: int
    active_alerts: int
    attack_distribution: list[AttackDistItem]
    severity_distribution: list[SeverityDistItem]
    traffic_over_time: list[TrafficPoint]
    top_suspicious_ips: list[TopIp]
    recent_incidents: list[RecentItem]
    recent_alerts: list[RecentItem]