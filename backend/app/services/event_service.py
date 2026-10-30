"""Event ingestion: classify a raw flow, persist NetworkEvent + Alert."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import Alert, AlertStatus, NetworkEvent, ThreatType
from ..models.network_event import NetworkEvent as NE
from ..monitor.detector import rule_hints_for, severity_for
from ..ml.inference import classify_row
from ..ml import LABEL_TO_STR

logger = logging.getLogger("sentinel.events")

_KNOWN_THREATS = {
    "port_scan", "brute_force", "ddos", "abnormal",
}


def ingest_flow(db: Session, flow: dict) -> NetworkEvent | None:
    """Persist a completed flow summary and raise an alert if warranted."""
    features = flow.get("features") or {}
    row = {
        "src_ip": flow.get("src_ip"),
        "dst_ip": flow.get("dst_ip"),
        "protocol": flow.get("protocol", "other"),
        "src_port": int(flow.get("src_port", 0) or 0),
        "dst_port": int(flow.get("dst_port", 0) or 0),
        "duration": float(features.get("duration", 0.0) or 0.0),
        "packet_count": int(flow.get("packet_count", 0) or 0),
        "bytes_sent": float(flow.get("bytes_sent", 0.0) or 0.0),
        "bytes_recv": float(flow.get("bytes_recv", 0.0) or 0.0),
    }
    result = classify_row({**row, "features": features})
    threat = result["threat_type"]
    hints = flow.get("hints")

    evt = NE(
        timestamp=datetime.now(timezone.utc),
        src_ip=row["src_ip"],
        dst_ip=row["dst_ip"],
        protocol=row["protocol"],
        src_port=row["src_port"],
        dst_port=row["dst_port"],
        bytes_sent=row["bytes_sent"],
        bytes_recv=row["bytes_recv"],
        packet_count=row["packet_count"],
        duration=row["duration"],
        features_json=features,
        threat_type=threat,
        threat_score=result["threat_score"],
        severity=severity_for(threat),
        rule_hits=_hints_list(hints),
    )
    db.add(evt)
    db.flush()

    if threat in _KNOWN_THREATS:
        _create_alert(db, evt, threat)
    return evt


def _hints_list(hints) -> list:
    if not hints:
        return []
    active = [k for k, v in hints.__dict__.items() if v]
    return active or []


def _create_alert(db: Session, evt: NetworkEvent, threat: str) -> Alert:
    info = rule_hints_for(threat)
    title = {
        "port_scan": f"Possible port scan from {evt.src_ip}",
        "brute_force": f"Suspected brute-force toward {evt.dst_ip}:{evt.dst_port}",
        "ddos": f"Possible DDoS / flood toward {evt.dst_ip}",
        "abnormal": f"Abnormal traffic {evt.src_ip} -> {evt.dst_ip}",
    }.get(threat, f"{threat} activity")
    description = (
        f"ML classified this flow as '{threat}' (score "
        f"{evt.threat_score:.3f}) matching rule {info['rule_name']}. "
        f"src={evt.src_ip} dst={evt.dst_ip}:{evt.dst_port} protocol={evt.protocol}."
    )
    alert = Alert(
        event_id=evt.id,
        title=title,
        description=description,
        rule_name=info["rule_name"],
        severity=info["severity"],
        status=AlertStatus.OPEN,
        score=evt.threat_score,
        source_ip=evt.src_ip,
        dst_ip=evt.dst_ip,
        protocol=evt.protocol,
    )
    db.add(alert)
    db.flush()
    return alert