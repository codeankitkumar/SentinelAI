"""Monitoring control endpoints: live capture, ingest a synthetic flow, stats."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..config import settings
from ..core.deps import _db, AdminDep, AnalystDep
from ..monitor.capture import capture_available, run_capture
from ..monitor.analyzer import FlowAggregator, analyze_flow_features
from ..services.event_service import ingest_flow
from ..models import NetworkEvent

router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.get("/capture")
def capture_status(_: AnalystDep) -> dict:
    return {
        "enabled": settings.network_monitor_enabled,
        "available": capture_available(),
        "interface": settings.monitor_interface,
        "message": (
            "Live capture is disabled. Enable NETWORK_MONITOR_ENABLED=true only "
            "in an authorized lab environment."
            if not settings.network_monitor_enabled else
            "Live capture enabled (authorized lab)."
        ),
    }


@router.post("/capture/start")
def start_capture(_: AdminDep, db: _db) -> dict:
    """Start a synchronous capture session (blocking) — not for web requests.

    In production this runs in a worker process streaming into the aggregator.
    Here we validate config and raise if capture is unavailable so the UI can
    surface the lab-requirement clearly.
    """
    if not settings.network_monitor_enabled:
        raise HTTPException(
            status_code=400,
            detail="Live capture disabled. See docs/SECURITY_LAB.md for the "
            "authorized-lab requirements before enabling.",
        )
    if not capture_available():
        raise HTTPException(status_code=400, detail="Scapy not available in this environment.")

    aggregator = FlowAggregator(idle_timeout=settings.flow_idle_timeout)

    def _on_flow(flow: dict):
        ingested = ingest_flow(db, aggregator._finalize(flow.copy()))
        return ingested

    # run_capture expects a callback taking a packet summary; aggregate then ingest.
    def _handler(pkt: dict):
        completed = aggregator.add_packet(pkt)
        if completed:
            ingest_flow(db, completed)

    return {
        "started": True,
        "note": "Use /monitor/simulate in the demo, or a worker capture loop.",
        "_handler": _handler,
    }


@router.post("/simulate")
def simulate_flow(payload: dict, _: AdminDep, db: _db) -> dict:
    """Ingest one synthetic flow for testing/demos (never real traffic)."""
    flow = _normalize_flow(payload)
    evt = ingest_flow(db, flow)
    db.commit()
    return {"event_id": evt.id if evt else None, "threat": evt.threat_type if evt else None}


@router.get("/summary")
def summary(_: AnalystDep, db: _db) -> dict:
    total = db.query(NetworkEvent).count()
    return {"total_events": total, "monitor_enabled": settings.network_monitor_enabled}


def _normalize_flow(payload: dict) -> dict:
    """Build a flow dict (with features) from a minimal submitted payload."""
    duration = float(payload.get("duration", 0))
    packet_count = int(payload.get("packet_count", 1) or 1)
    sent = float(payload.get("bytes_sent", 0))
    recv = float(payload.get("bytes_recv", 0))
    total = sent + recv
    proto = payload.get("protocol", "tcp")
    enc = {"tcp": 0, "udp": 1, "icmp": 2}.get(proto, 3)
    flow = payload.copy()
    flow.setdefault("src_port", 0)
    flow.setdefault("dst_port", 0)
    flow["features"] = {
        "duration": duration, "packet_count": packet_count,
        "bytes_sent": sent, "bytes_recv": recv, "bytes_total": total,
        "bytes_per_packet": total / packet_count, "bytes_ratio": recv / (sent + 1),
        "src_port": flow["src_port"], "dst_port": flow["dst_port"],
        "protocol_encoded": enc, "is_icmp": 1.0 if proto == "icmp" else 0.0,
        "packets_per_second": packet_count / duration if duration else 0,
        "bytes_per_second": total / duration if duration else 0,
    }
    return flow