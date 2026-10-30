"""Scapy-based packet capture loop (OPTIONAL, authorized lab only).

This module should only ever run with explicit authorization on a network you
control. Enable it via ``NETWORK_MONITOR_ENABLED=true`` in .env. For most CI/
demo scenarios we use the demo generator instead, so Scapy is imported lazily.
"""
from __future__ import annotations

import logging

from ..config import settings

logger = logging.getLogger("sentinel.monitor")

# Guard: refuse to even import scapy-driven logic unless enabled + explicit.
if settings.network_monitor_enabled:
    try:
        from scapy.all import sniff  # noqa: F401
        _SCAPY_OK = True
    except Exception as exc:  # pragma: no cover
        _SCAPY_OK = False
        logger.warning("Scapy unavailable: %s", exc)
else:
    _SCAPY_OK = False


def capture_available() -> bool:
    return _SCAPY_OK


def _packet_to_summary(pkt) -> dict | None:
    """Convert a Scapy packet into a minimal flow-summary dict (authorized lab)."""
    try:
        from scapy.layers.inet import IP, TCP, UDP, ICMP
    except Exception:
        return None
    if pkt.haslayer(IP):
        src = pkt[IP].src
        dst = pkt[IP].dst
        proto = "tcp" if pkt.haslayer(TCP) else "udp" if pkt.haslayer(UDP) else "icmp" if pkt.haslayer(ICMP) else "other"
        src_port = dst_port = 0
        if pkt.haslayer(TCP):
            src_port = pkt[TCP].sport
            dst_port = pkt[TCP].dport
        elif pkt.haslayer(UDP):
            src_port = pkt[UDP].sport
            dst_port = pkt[UDP].dport
        length = int(getattr(pkt, "len", 0) or 0)
        return {
            "src_ip": src,
            "dst_ip": dst,
            "protocol": proto,
            "src_port": src_port,
            "dst_port": dst_port,
            "bytes_sent": length,
            "bytes_recv": 0,
        }
    return None


def run_capture(on_flow, count: int = 0, timeout: int | None = None) -> None:
    """Sniff packets on the configured interface and feed a FlowAggregator.

    ``on_flow`` is a callback receiving a completed flow summary. This is only
    meaningful when the operator has authorized the capture (checked here).
    """
    if not _SCAPY_OK:
        raise RuntimeError(
            "Live capture disabled. Set NETWORK_MONITOR_ENABLED=true only in an "
            "authorized lab environment with Scapy installed."
        )
    from scapy.all import sniff  # local import avoids import cost otherwise

    aggregator = on_flow.__self__._flows if hasattr(on_flow, "__self__") else None

    def _handler(pkt):
        summary = _packet_to_summary(pkt)
        if summary is None:
            return
        on_flow(summary)

    sniff(
        iface=settings.monitor_interface or None,
        prn=_handler,
        store=False,
        count=count if count else None,
        timeout=timeout,
    )