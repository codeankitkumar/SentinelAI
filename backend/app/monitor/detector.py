"""Rule-based detection layer.

Independent, explainable detections that complement the ML model. Each rule
returns a (title, severity, score, description) advisory so alerts are
auditable and analyst-friendly.

NOTE: This performs *analysis* on already-collected flow summaries. It never
injects or acts on live network traffic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..ml import LABEL_TO_STR as _L

# Well-known authentication ports often targeted by brute force.
AUTH_PORTS = {21, 22, 23, 3389, 3306, 5432, 5900}


@dataclass
class DetectionRule:
    name: str
    severity: str
    score: float
    title: str
    description: str


def severity_for(threat_type: str) -> str:
    """Map a threat classification to an alert severity."""
    return {
        "normal": "info",
        "port_scan": "high",
        "brute_force": "high",
        "ddos": "critical",
        "abnormal": "medium",
    }.get(threat_type, "low")


def detect_threat_from_event(event: dict[str, Any]) -> DetectionRule | None:
    """Derive an advisory from an analyzed event summary."""
    threat_type = event.get("threat_type", "normal")
    score = float(event.get("threat_score", 0.0))
    dst_port = int(event.get("dst_port", 0) or 0)
    src = event.get("src_ip", "?")
    dst = event.get("dst_ip", "?")

    if threat_type == "port_scan":
        return DetectionRule(
            name="Network::PortScan",
            severity="high",
            score=score,
            title=f"Possible port scan from {src}",
            description=(
                f"Flow from {src} toward {dst} shows characteristics consistent "
                "with a port sweep (many distinct low ports / short-lived "
                "connections). Verify whether this scan is authorized."
            ),
        )
    if threat_type == "brute_force":
        service = dst_port
        return DetectionRule(
            name="Auth::BruteForce",
            severity="high",
            score=score,
            title=f"Suspected brute-force login against port {service}",
            description=(
                f"Elevated connection rate from {src} to {dst}:{service} is a "
                "classic sign of credential stuffing. Check auth logs and "
                "review account lockouts."
            ),
        )
    if threat_type == "ddos":
        return DetectionRule(
            name="Network::DDoS",
            severity="critical",
            score=score,
            title=f"Possible DDoS / flood toward {dst}",
            description=(
                f"High packet/byte rate observed targeting {dst}. Correlate "
                "with load balancer and firewall counters before response."
            ),
        )
    if threat_type == "abnormal":
        return DetectionRule(
            name="Network::AbnormalTraffic",
            severity="medium",
            score=score,
            title=f"Abnormal flow {src} -> {dst}",
            description=(
                "Unusual flow asymmetry or protocol pattern detected. " 
                "Investigate sources and destination services."
            ),
        )
    return None


# Threshold map used by the flow analyzer to flag raw events pre-classification.
def rule_hints_for(threat_type: str) -> dict:
    return {
        "rule_name": {
            "port_scan": "Network::PortScan",
            "brute_force": "Auth::BruteForce",
            "ddos": "Network::DDoS",
            "abnormal": "Network::AbnormalTraffic",
        }.get(threat_type, "ML::Classification"),
        "severity": severity_for(threat_type),
    }