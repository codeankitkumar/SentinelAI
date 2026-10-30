"""Dashboard aggregation endpoint."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from sqlalchemy import func

from ..core.deps import _db, AnalystDep
from ..models import Alert, Incident, NetworkEvent
from ..schemas.dashboard import (
    AttackDistItem,
    DashboardStats,
    RecentItem,
    SeverityDistItem,
    StatCard,
    TopIp,
    TrafficPoint,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Severity ordering/colors for the UI.
SEV_ORDER = ["critical", "high", "medium", "low", "info"]


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(_: AnalystDep, db: _db) -> DashboardStats:
    total_events = db.query(NetworkEvent).count()
    total_alerts = db.query(Alert).count()
    critical_incidents = db.query(Incident).filter(
        Incident.severity == "critical"
    ).count()
    active_alerts = db.query(Alert).filter(
        Alert.status.in_(["open", "acknowledged"])
    ).count()

    attack_rows = (
        db.query(NetworkEvent.threat_type, func.count(NetworkEvent.id))
        .filter(NetworkEvent.threat_type != "normal")
        .group_by(NetworkEvent.threat_type).all()
    )
    attack_distribution = [
        AttackDistItem(threat_type=t, count=c) for t, c in attack_rows
    ]

    sev_rows = (
        db.query(Alert.severity, func.count(Alert.id)).group_by(Alert.severity).all()
    )
    sev_map = dict(sev_rows)
    severity_distribution = [
        SeverityDistItem(severity=s, count=sev_map.get(s, 0)) for s in SEV_ORDER
    ]

    traffic_over_time = _traffic_series(db)

    top_ips = (
        db.query(Alert.source_ip, func.count(Alert.id))
        .filter(Alert.source_ip.isnot(None))
        .group_by(Alert.source_ip)
        .order_by(func.count(Alert.id).desc())
        .limit(8).all()
    )
    top_suspicious_ips = []
    for ip, cnt in top_ips:
        row = db.query(Alert).filter(Alert.source_ip == ip).first()
        sev = row.severity if row else "low"
        top_suspicious_ips.append(TopIp(ip=ip, count=int(cnt), severity=sev))

    recent_alerts = (
        db.query(Alert).order_by(Alert.timestamp.desc()).limit(6).all()
    )
    recent_incidents = (
        db.query(Incident).order_by(Incident.updated_at.desc()).limit(6).all()
    )

    return DashboardStats(
        total_events=total_events,
        total_alerts=total_alerts,
        critical_incidents=critical_incidents,
        active_alerts=active_alerts,
        attack_distribution=attack_distribution,
        severity_distribution=severity_distribution,
        traffic_over_time=traffic_over_time,
        top_suspicious_ips=top_suspicious_ips,
        recent_incidents=[
            RecentItem(id=i.id, title=i.title, severity=i.severity,
                       status=i.status, source_ip=None,
                       timestamp=i.updated_at) for i in recent_incidents
        ],
        recent_alerts=[
            RecentItem(id=a.id, title=a.title, severity=a.severity,
                       status=a.status, source_ip=a.source_ip,
                       timestamp=a.timestamp, rule_name=a.rule_name) for a in recent_alerts
        ],
    )


def _traffic_series(db) -> list[TrafficPoint]:
    """Hourly event/alert counts over the last 24h."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=23)
    buckets = []
    for h in range(24):
        bucket_floor = start + timedelta(hours=h)
        bucket_ceil = bucket_floor + timedelta(hours=1)
        events = db.query(NetworkEvent).filter(
            NetworkEvent.timestamp >= bucket_floor, NetworkEvent.timestamp < bucket_ceil
        ).count()
        alerts = db.query(Alert).filter(
            Alert.timestamp >= bucket_floor, Alert.timestamp < bucket_ceil
        ).count()
        buckets.append(TrafficPoint(
            bucket=bucket_floor.strftime("%H:%M"), events=events, alerts=alerts
        ))
    return buckets