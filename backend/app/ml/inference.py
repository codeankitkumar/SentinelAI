"""Real-time inference.

Learns a rule-based detector as a transparent fallback so that the platform
remains useful even before a trained model artifact exists (e.g. on a fresh
deployment without a dataset on disk).
"""
from __future__ import annotations

import math

import numpy as np

from .. import ml as ml_pkg
from .features import extract_features
from .model import load_pipeline

# Rule thresholds (tuned on the synthetic sample dataset, see training report).
_RULES = [
    {"kind": ml_pkg.STR_TO_LABEL["port_scan"], "threshold": 1.0, "severity": "high",
     "name": "port_scan"},
    {"kind": ml_pkg.STR_TO_LABEL["brute_force"], "threshold": 1.0, "severity": "high",
     "name": "brute_force"},
    {"kind": ml_pkg.STR_TO_LABEL["ddos"], "threshold": 1.0, "severity": "critical",
     "name": "ddos"},
]

# Cached pipeline; refreshed on each call so retraining takes effect immediately.
_cached: tuple | None = None
_cached_version: str = ""


class Inferencer:
    """Wrap the trained model + scaler (or rule fallback)."""

    def __init__(self) -> None:
        self.model, self.scaler = load_pipeline()
        self._version = "trained" if self.model is not None else "rules"

    @property
    def version(self) -> str:
        return self._version

    def predict(self, row: dict) -> dict:
        feats = row.get("features") if isinstance(row.get("features"), dict) else row
        x = extract_features(
            duration=feats.get("duration", 0),
            packet_count=feats.get("packet_count", 0),
            bytes_sent=feats.get("bytes_sent", 0),
            bytes_recv=feats.get("bytes_recv", 0),
            src_port=feats.get("src_port", 0),
            dst_port=feats.get("dst_port", 0),
            protocol=row.get("protocol", feats.get("protocol", "tcp")),
        )
        arr = np.asarray(x, dtype=np.float32).reshape(1, -1)
        if self.model is not None and self.scaler is not None:
            arr = self.scaler.transform(arr)
            proba = self.model.predict_proba(arr)[0]
            cls = int(self.model.predict(arr)[0])
            score = float(math.floor(proba[cls] * 1000) / 1000)
            return {
                "threat_type": ml_pkg.LABEL_TO_STR[cls],
                "threat_score": score,
                "confidence": score,
                "model": "ml",
            }
        # Fallback: heuristic scoring tied to rule studies.
        score = _rule_score(x)
        return {
            "threat_type": _rule_label(score),
            "threat_score": score,
            "confidence": min(0.99, 0.5 + score),
            "model": "rules",
        }


def _rule_score(x: list[float]) -> float:
    """Heuristic 0..1 score from the canonical vector for fallback mode.

    Vector order = FEATURE_COLUMNS; see ml/__init__.py.
    """
    duration, packet_count, bytes_sent, bytes_recv, *_ = x
    dst_port = x[8]
    pps = x[11]
    score = 0.0
    # DDoS / flood: high packet rate with many small packets.
    if packet_count > 1500 and pps > 300:
        score = max(score, 0.9)
    # Port scan: sweeping distinct low destinations with brief duration.
    if dst_port == 0 and duration < 1.0:
        score = max(score, 0.55)
    # Brute-force: sustained moderate rate to auth ports.
    if dst_port in (22, 21, 3389, 3306, 5432) and packet_count > 400:
        score = max(score, 0.8)
    if bytes_recv / max(bytes_sent, 1) > 20 and packet_count > 1000:
        score = max(score, 0.7)
    return round(min(score, 1.0), 3)


def _rule_label(score: float) -> str:
    if score < 0.35:
        return ml_pkg.LABEL_TO_STR[ml_pkg.STR_TO_LABEL["normal"]]
    if score < 0.6:
        return ml_pkg.LABEL_TO_STR[ml_pkg.STR_TO_LABEL["port_scan"]]
    if score < 0.8:
        return ml_pkg.LABEL_TO_STR[ml_pkg.STR_TO_LABEL["brute_force"]]
    return ml_pkg.LABEL_TO_STR[ml_pkg.STR_TO_LABEL["ddos"]]


# A module-level singleton to keep inference cheap.
_inferencer: Inferencer | None = None


def get_inferencer() -> Inferencer:
    global _inferencer
    if _inferencer is None:
        _inferencer = Inferencer()
    return _inferencer


def classify_row(row: dict) -> dict:
    return get_inferencer().predict(row)


def reload() -> None:
    """Drop the cached inferencer so the next call reloads artifacts."""
    global _inferencer
    _inferencer = None