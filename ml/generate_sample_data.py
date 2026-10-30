"""Generate a synthetic netflow training dataset (authorized, simulated).

This lets the whole ML pipeline be trained and evaluated offline with NO live
packet capture and no external dataset download. For real data, use
``prepare_dataset.py`` with CIC-IDS2017 / UNSW-NB15 (see docs/DATASETS.md).

Output columns match the canonical feature schema used by the runtime
(backend/app/ml/__init__.py FEATURE_COLUMNS) plus a ``label`` column.
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

import numpy as np
import pandas as pd

OUT_DEFAULT = Path(__file__).resolve().parent / "datasets" / "sample_netflow.csv"

CLASSES = ["normal", "port_scan", "brute_force", "ddos", "abnormal"]


def _normal() -> list[float]:
    duration = random.uniform(0.1, 300)
    packets = max(1, int(np.random.poisson(duration * random.uniform(1, 8))))
    sent = random.uniform(32, 2000) * packets
    recv = random.uniform(32, 2000) * packets * random.uniform(0.2, 1.2)
    src_port = random.randint(1024, 65000)
    dst_port = random.choice([80, 443, 53, 22, 8080, 993, 3306, random.randint(1024, 49000)])
    proto = random.choice(["tcp", "tcp", "tcp", "udp"])
    return _to_row(duration, packets, sent, recv, src_port, dst_port, proto)


def _port_scan() -> list[float]:
    # One representative scan flow: very short duration, low ports, few packets.
    dst_port = int(np.random.choice(range(1, 1200)))
    duration = random.uniform(0.005, 0.9)
    packets = int(random.uniform(1, 6))
    sent = random.uniform(40, 300)
    recv = random.uniform(0, 60)
    return _to_row(
        duration, packets, sent, recv,
        random.randint(1024, 40000), dst_port, "tcp",
    )


def _brute_force() -> list[float]:
    return _to_row(
        random.uniform(20, 400),
        int(random.uniform(400, 8000)),
        random.uniform(800, 4000),
        random.uniform(2000, 8000),
        random.randint(1024, 40000),
        random.choice([22, 21, 3389, 3306, 5432]),
        "tcp",
    )


def _ddos() -> list[float]:
    # Flood: very high packet rate, small packets.
    duration = random.uniform(5, 120)
    packets = int(random.uniform(2000, 120000))
    sent = random.uniform(40, 200) * packets
    recv = random.uniform(0, 100)
    return _to_row(
        duration, packets, sent, recv,
        random.randint(1024, 65000), random.choice([80, 443, 53]),
        random.choice(["tcp", "udp"]),
    )


def _abnormal() -> list[float]:
    # Asymmetric / unusual traffic that isn't in the three headline attacks.
    duration = random.uniform(1, 90)
    packets = int(random.uniform(50, 600))
    sent = random.uniform(10, 100)
    recv = random.uniform(3000, 200000)  # large inbound response imbalance
    dst_port = random.choice([123, 137, 445, 6667, 6881])
    return _to_row(
        duration, packets, sent, recv,
        random.randint(1024, 65000), dst_port, random.choice(["udp", "tcp"]),
    )


def _to_row(duration, packets, sent, recv, src_port, dst_port, proto) -> list[float]:
    duration = max(duration, 0.001)
    packets = max(packets, 1)
    sent = max(sent, 0.0)
    recv = max(recv, 0.0)
    total = sent + recv
    proto_enc = {"tcp": 0, "udp": 1, "icmp": 2}.get(proto, 3)
    is_icmp = 1.0 if proto == "icmp" else 0.0
    return [
        round(duration, 4),
        packets,
        round(sent, 2),
        round(recv, 2),
        round(total, 2),
        round(total / packets, 4),
        round(recv / (sent + 1.0), 4),
        src_port,
        dst_port,
        proto_enc,
        is_icmp,
        round(packets / duration, 4),
        round(total / duration, 2),
    ]


COLUMNS = [
    "duration", "packet_count", "bytes_sent", "bytes_recv", "bytes_total",
    "bytes_per_packet", "bytes_ratio", "src_port", "dst_port",
    "protocol_encoded", "is_icmp", "packets_per_second", "bytes_per_second",
]

GENERATORS = {
    "normal": _normal,
    "port_scan": _port_scan,
    "brute_force": _brute_force,
    "ddos": _ddos,
    "abnormal": _abnormal,
}


def generate(n_samples: int, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)
    rows: list[list[float]] = []
    labels: list[str] = []
    # Attack labels are somewhat rarer than normal but all represented.
    weights = {"normal": 1.0, "port_scan": 0.85, "brute_force": 0.7, "ddos": 0.65, "abnormal": 0.6}
    classes = list(weights.keys())
    probs = [weights[c] / sum(weights.values()) for c in classes]
    while len(rows) < n_samples:
        cls = random.choices(classes, weights=probs, k=1)[0]
        candidate = GENERATORS[cls]()
        rows.append(candidate)
        labels.append(cls)
    if len(rows) > n_samples:
        rows = rows[:n_samples]
        labels = labels[:n_samples]
    return pd.DataFrame(rows, columns=COLUMNS).assign(label=labels)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic SentinelAI netflow dataset")
    parser.add_argument("--out", type=str, default=str(OUT_DEFAULT))
    parser.add_argument("--n", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df = generate(args.n, seed=args.seed)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows -> {out}")
    print(df["label"].value_counts().to_string())


if __name__ == "__main__":
    main()