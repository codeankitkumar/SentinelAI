"""Feature engineering.

Defines the canonical numeric feature vector used both for training and for
real-time inference so that the two are always consistent. When ingesting a
public dataset such as CIC-IDS2017 or UNSW-NB15, run the mapping script in
``ml/prepare_dataset.py`` which reduces the raw columns to this schema.
"""
from __future__ import annotations

import numpy as np

from . import FEATURE_COLUMNS

# Protocol encoding used consistently across training/inference.
PROTOCOL_ENCODING = {"tcp": 0, "udp": 1, "icmp": 2}
PROTOCOL_DEFAULT = 3


def encode_protocol(protocol: str) -> int:
    return PROTOCOL_ENCODING.get((protocol or "").lower(), PROTOCOL_DEFAULT)


def extract_features(
    *,
    duration: float,
    packet_count: int,
    bytes_sent: float,
    bytes_recv: float,
    src_port: int,
    dst_port: int,
    protocol: str,
) -> list[float]:
    """Return the canonical feature vector for a single flow."""
    duration = float(max(duration, 0.0))
    packet_count = float(max(packet_count, 0))
    bytes_sent = float(max(bytes_sent, 0.0))
    bytes_recv = float(max(bytes_recv, 0.0))
    bytes_total = bytes_sent + bytes_recv
    is_icmp = 1.0 if (protocol or "").lower() == "icmp" else 0.0

    # Guard against division by zero.
    bytes_per_packet = bytes_total / packet_count if packet_count > 0 else 0.0
    bytes_ratio = bytes_recv / (bytes_sent + 1.0)
    packets_per_second = packet_count / duration if duration > 0 else 0.0
    bytes_per_second = bytes_total / duration if duration > 0 else 0.0

    return [
        duration,
        packet_count,
        bytes_sent,
        bytes_recv,
        bytes_total,
        bytes_per_packet,
        bytes_ratio,
        float(src_port),
        float(dst_port),
        float(encode_protocol(protocol)),
        is_icmp,
        packets_per_second,
        bytes_per_second,
    ]


def feature_array_from_row(row: dict) -> np.ndarray:
    """Build a feature vector from a dict that already follows FEATURE_COLUMNS."""
    vector = [float(row.get(col, 0.0) or 0.0) for col in FEATURE_COLUMNS]
    return np.asarray(vector, dtype=np.float32).reshape(1, -1)