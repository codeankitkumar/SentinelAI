"""Flow aggregation and feature computation.

`FlowAggregator` buckets raw 5-tuple flows by key and computes the canonical
feature vector plus lightweight anomaly hints. It is pure computation over
already-collected summaries (no live capture here).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import detector
from ..ml.features import extract_features

AUTH_PORTS = {21, 22, 23, 3389, 3306, 5432, 5900}


@dataclass
class ThreatHints:
    port_scan: bool = False
    brute_force: bool = False
    ddos: bool = False
    abnormal: bool = False


def analyze_flow_features(summary: dict) -> ThreatHints:
    """Lightweight rule hints independent of the ML model (explainability)."""
    hints = ThreatHints()
    packets = int(summary.get("packet_count", 0) or 0)
    pps = summary.get("packets_per_second", 0.0) or 0.0
    duration = summary.get("duration", 0.0) or 0.0
    dst_port = int(summary.get("dst_port", 0) or 0)
    bpp = summary.get("bytes_per_packet", 0.0) or 0.0

    if packets > 1500 and pps > 300:
        hints.ddos = True
    if packets > 400 and dst_port in AUTH_PORTS:
        hints.brute_force = True
    if duration < 1.0 and dst_port < 1024 and packets < 20:
        hints.port_scan = True
    if summary.get("bytes_total", 0.0) and (bpp < 20 or bpp > 200000):
        hints.abnormal = True
    return hints


@dataclass
class FlowAggregator:
    idle_timeout: float = 60.0
    _flows: dict = field(default_factory=dict)

    def _key(self, flow: dict) -> str:
        return f"{flow['src_ip']}|{flow['dst_ip']}|{flow['protocol']}|{flow['dst_port']}"

    def add_packet(self, packet: dict) -> dict | None:
        """Accumulate a packet summary; returns a completed flow when idle.

        In real deployments this is fed from the Scapy capture loop; in the
        demo/seed path we feed synthetic flow summaries directly.
        """
        key = self._key(packet)
        now = time.time()
        flow = self._flows.get(key)
        if flow is None:
            flow = {
                "src_ip": packet["src_ip"],
                "dst_ip": packet["dst_ip"],
                "protocol": packet["protocol"],
                "src_port": packet.get("src_port", 0),
                "dst_port": packet.get("dst_port", 0),
                "packet_count": 0,
                "bytes_sent": 0.0,
                "bytes_recv": 0.0,
                "first_seen": now,
                "last_seen": now,
            }
            self._flows[key] = flow

        flow["packet_count"] += 1
        flow["bytes_sent"] += float(packet.get("bytes_sent", 0.0))
        flow["bytes_recv"] += float(packet.get("bytes_recv", 0.0))
        flow["last_seen"] = now

        if now - flow["last_seen"] > self.idle_timeout or now - flow["first_seen"] > 600:
            return self._finalize(flow)
        return None

    def _finalize(self, flow: dict) -> dict:
        key = f"{flow['src_ip']}|{flow['dst_ip']}|{flow['protocol']}|{flow['dst_port']}"
        self._flows.pop(key, None)
        summary = dict(flow)
        summary["duration"] = flow["last_seen"] - flow["first_seen"]
        vector = extract_features(
            duration=summary["duration"],
            packet_count=summary["packet_count"],
            bytes_sent=summary["bytes_sent"],
            bytes_recv=summary["bytes_recv"],
            src_port=summary["src_port"],
            dst_port=summary["dst_port"],
            protocol=summary["protocol"],
        )
        feature_names = [
            "duration", "packet_count", "bytes_sent", "bytes_recv", "bytes_total",
            "bytes_per_packet", "bytes_ratio", "src_port", "dst_port",
            "protocol_encoded", "is_icmp", "packets_per_second", "bytes_per_second",
        ]
        summary["features"] = dict(zip(feature_names, vector))
        summary["bytes_total"] = vector[4]
        summary["bytes_per_packet"] = vector[5]
        summary["packets_per_second"] = vector[11]
        summary["hints"] = analyze_flow_features(summary)
        return summary