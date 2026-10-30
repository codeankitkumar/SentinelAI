"""Database bootstrap: create tables, seed admin/analyst users and demo data."""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .config import settings
from .core.security import hash_password
from .database import Base, engine
from .models import (
    Alert,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    NetworkEvent,
    User,
    UserRole,
)
from .services.event_service import ingest_flow

logger = logging.getLogger("sentinel.seed")

_DEMO_IPS = [
    "10.0.0.10", "10.0.0.11", "10.0.0.12", "10.0.0.14", "10.0.0.20",
    "10.0.4.15", "10.0.4.23", "10.0.8.2", "172.16.100.5", "172.16.200.9",
    "198.51.100.10", "198.51.100.44", "203.0.113.7", "192.0.2.99", "198.51.100.120",
]
_INTERNAL = ["10.0.0.10", "10.0.0.11", "10.0.0.12", "10.0.0.14", "172.16.100.5"]


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")


def seed_users(db: Session) -> None:
    if db.query(User).filter(User.username == "admin").first() is None:
        db.add(User(
            username="admin",
            email="admin@sentinel.local",
            full_name="Sentinel Administrator",
            hashed_password=hash_password("Admin@12345"),
            role=UserRole.ADMIN,
            is_active=True,
        ))
    if db.query(User).filter(User.username == "analyst").first() is None:
        db.add(User(
            username="analyst",
            email="analyst@sentinel.local",
            full_name="SOC Analyst",
            hashed_password=hash_password("Analyst@12345"),
            role=UserRole.ANALYST,
            is_active=True,
        ))
    db.commit()
def _random_flow(now: datetime) -> dict:
    r = random.random()
    if r < 0.55:
        return _normal_flow(now)
    if r < 0.65:
        return _scan_flow(now)
    if r < 0.75:
        return _brute_flow(now)
    if r < 0.82:
        return _ddos_flow(now)
    return _abnormal_flow(now)


def _normal_flow(now: datetime) -> dict:
    src = random.choice(_INTERNAL)
    dst = random.choice([ip for ip in _DEMO_IPS if ip != src])
    duration = random.uniform(0.2, 200)
    packets = int(duration * random.uniform(1, 6)) + 1
    sent = random.uniform(200, 1600) * packets
    recv = random.uniform(200, 1600) * packets
    proto = random.choice(["tcp", "tcp", "udp"])
    return _flow(src, dst, proto, random.randint(15000, 65000),
                 random.choice([80, 443, 53, 22, 8080, 3306, random.randint(1024, 49000)]),
                 duration, packets, sent, recv)


def _scan_flow(now: datetime) -> dict:
    src = random.choice([ip for ip in _DEMO_IPS if ip not in _INTERNAL] or _DEMO_IPS)
    dst = random.choice(_INTERNAL)
    return _flow(src, dst, "tcp", random.randint(1024, 40000),
                 random.randint(1, 1024), random.uniform(0.004, 0.7),
                 random.randint(1, 6), random.uniform(40, 300), random.uniform(0, 60))


def _brute_flow(now: datetime) -> dict:
    src = random.choice([ip for ip in _DEMO_IPS if ip not in _INTERNAL] or _DEMO_IPS)
    dst = random.choice(_INTERNAL)
    duration = random.uniform(20, 300)
    packets = int(random.uniform(400, 6000))
    proto = "tcp"
    port = random.choice([22, 21, 3389, 3306, 5432])
    return _flow(src, dst, proto, random.randint(1024, 40000), port,
                 duration, packets, random.uniform(800, 4000), random.uniform(2000, 8000))


def _ddos_flow(now: datetime) -> dict:
    src = random.choice([ip for ip in _DEMO_IPS if ip not in _INTERNAL] or _DEMO_IPS)
    dst = random.choice(_INTERNAL)
    duration = random.uniform(5, 120)
    packets = int(random.uniform(2000, 90000))
    return _flow(src, dst, random.choice(["tcp", "udp"]), random.randint(1024, 65000),
                 random.choice([80, 443, 53]), duration, packets, random.uniform(40, 200) * packets,
                 random.uniform(0, 100))


def _abnormal_flow(now: datetime) -> dict:
    src = random.choice(_DEMO_IPS)
    dst = random.choice([ip for ip in _DEMO_IPS if ip != src])
    duration = random.uniform(1, 90)
    packets = int(random.uniform(50, 600))
    return _flow(src, dst, random.choice(["udp", "tcp"]), random.randint(1024, 65000),
                 random.choice([123, 137, 445, 6667, 6881]), duration, packets,
                 random.uniform(10, 100), random.uniform(3000, 200000))
def _flow(src, dst, proto, sp, dp, duration, packets, sent, recv) -> dict:
    total = sent + recv
    bpp = total / max(packets, 1)
    enc = {"tcp": 0, "udp": 1, "icmp": 2}.get(proto, 3)
    return {
        "src_ip": src,
        "dst_ip": dst,
        "protocol": proto,
        "src_port": int(sp),
        "dst_port": int(dp),
        "packet_count": packets,
        "bytes_sent": round(sent, 2),
        "bytes_recv": round(recv, 2),
        "duration": round(max(duration, 0.001), 4),
        "features": {
            "duration": round(max(duration, 0.001), 4),
            "packet_count": packets,
            "bytes_sent": round(sent, 2),
            "bytes_recv": round(recv, 2),
            "bytes_total": round(total, 2),
            "bytes_per_packet": round(bpp, 4),
            "bytes_ratio": round(recv / (sent + 1.0), 4),
            "src_port": int(sp),
            "dst_port": int(dp),
            "protocol_encoded": enc,
            "is_icmp": 1.0 if proto == "icmp" else 0.0,
            "packets_per_second": round(packets / max(duration, 0.001), 4),
            "bytes_per_second": round(total / max(duration, 0.001), 2),
        },
    }


def seed_demo_events(db: Session, n: int = 2000) -> None:
    """Insert synthetic events spread over the past 24h for a usable dashboard."""
    random.seed(7)
    now = datetime.now(timezone.utc)
    for i in range(n):
        ts = now - timedelta(minutes=int((i / n) * 24 * 60))
        flow = _random_flow(ts)
        _ingest_at(db, flow, ts)
    db.commit()
    logger.info("Seeded %d demo events.", n)


def _ingest_at(db: Session, flow: dict, ts: datetime) -> NetworkEvent | None:
    evt = ingest_flow(db, flow)
    if evt is None:
        return None
    evt.timestamp = ts
    return evt


def seed_demo_incidents(db: Session) -> None:
    """Create a few representative incidents from seeded alerts."""
    for src_ip in ["198.51.100.10", "203.0.113.7"]:
        alerts = (db.query(Alert)
                  .filter(Alert.source_ip == src_ip, Alert.severity.in_(["high", "critical"]))
                  .limit(3).all())
        if not alerts:
            continue
        incident = Incident(
            title=f"Investigation: suspicious source {src_ip}",
            description=(
                "Repeated high/critical alerts sourced from this IP. Assess "
                "whether the activity is authorized before any response action."
            ),
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.INVESTIGATING,
            assignee="SOC Analyst",
            alerts=alerts,
        )
        db.add(incident)
    db.commit()


def run_seed_if_needed() -> None:
    """Entrypoint called on startup when SEED_DEMO_DATA=true."""
    if not settings.seed_demo_data:
        logger.info("SEED_DEMO_DATA=false; skip demo seeding.")
        return
    from .database import SessionLocal as make_session
    db = make_session()
    try:
        seed_users(db)
        needs_events = db.query(NetworkEvent).count() == 0
        if needs_events:
            seed_demo_events(db, settings.seed_demo_events)
            seed_demo_incidents(db)
        else:
            logger.info("Demo events already present; skipping.")
    finally:
        db.close()