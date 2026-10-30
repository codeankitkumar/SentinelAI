"""Network monitoring engine.

Only process authorized/private traffic. See docs/SECURITY_LAB.md before
enabling live capture.
"""
from .detector import DetectionRule, detect_threat_from_event, severity_for
from .analyzer import FlowAggregator, analyze_flow_features, ThreatHints

__all__ = [
    "DetectionRule",
    "detect_threat_from_event",
    "severity_for",
    "FlowAggregator",
    "analyze_flow_features",
    "ThreatHints",
]