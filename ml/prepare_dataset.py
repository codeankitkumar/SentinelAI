"""Prepare a public dataset (CIC-IDS2017 / UNSW-NB15) for SentinelAI training.

Reduces a raw dataset to the canonical feature schema used at runtime:

    duration, packet_count, bytes_sent, bytes_recv, bytes_total,
    bytes_per_packet, bytes_ratio, src_port, dst_port, protocol_encoded,
    is_icmp, packets_per_second, bytes_per_second, label

Ground-truth labels are grouped into the five SentinelAI classes:
normal, port_scan, brute_force, ddos, abnormal.

See docs/DATASETS.md for download + licensing notes. Only machine-usable,
publicly released research datasets should be used (isolated lab use).

Usage:
    python prepare_dataset.py --dataset cic --input data/CIC-IDS2017.csv \
        --out datasets/cic_prepared.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "duration", "packet_count", "bytes_sent", "bytes_recv", "bytes_total",
    "bytes_per_packet", "bytes_ratio", "src_port", "dst_port",
    "protocol_encoded", "is_icmp", "packets_per_second", "bytes_per_second",
    "label",
]

# Map raw dataset labels -> SentinelAI class.
CIC_LABELS = {
    "Benign": "normal",
    "PortScan": "port_scan",
    "Nmap": "port_scan",
    "SSH-Patator": "brute_force",
    "FTP-Patator": "brute_force",
    "Web Attack-Brute Force": "brute_force",
    "DDoS": "ddos",
    "DoS Hulk": "ddos",
    "DoS GoldenEye": "ddos",
    "DoS slowloris": "ddos",
    "DoS Slowhttptest": "ddos",
    "Heartbleed": "ddos",
    "Infiltration": "abnormal",
    "Bot": "abnormal",
    "Web Attack - XSS": "abnormal",
    "Web Attack - SQL Injection": "abnormal",
}

UNSW_LABELS = {
    "Normal": "normal",
    "Fuzzers": "brute_force",
    "Analysis": "abnormal",
    "Backdoor": "abnormal",
    "DoS": "ddos",
    "Exploits": "abnormal",
    "Generic": "abnormal",
    "Reconnaissance": "port_scan",
    "Shellcode": "abnormal",
    "Worms": "ddos",
}


def prepare_cic(df: pd.DataFrame) -> pd.DataFrame:
    """CIC-IDS2017: space-separated header, many flow attributes."""
    df = df.dropna(how="all")
    df.columns = [c.strip() for c in df.columns]
    out = pd.DataFrame()
    out["duration"] = pd.to_numeric(df.get("Flow Duration"), errors="coerce") / 1_000_000.0
    out["packet_count"] = (
        pd.to_numeric(df.get("Total Fwd Packets"), errors="coerce") +
        pd.to_numeric(df.get("Total Backward Packets"), errors="coerce")
    )
    out["bytes_sent"] = pd.to_numeric(df.get("Total Length of Fwd Packets"), errors="coerce")
    out["bytes_recv"] = pd.to_numeric(df.get("Total Length of Bwd Packets"), errors="coerce")
    out["src_port"] = pd.to_numeric(df.get("Source Port"), errors="coerce")
    out["dst_port"] = pd.to_numeric(df.get("Destination Port"), errors="coerce")
    proto = df.get("Protocol")
    out["protocol_encoded"] = pd.to_numeric(proto, errors="coerce").map(
        {6: 0, 17: 1, 1: 2}).fillna(3)
    out["is_icmp"] = (pd.to_numeric(proto, errors="coerce") == 1).astype(float)
    raw_label = df.get("Label")
    out["label"] = raw_label.map(CIC_LABELS).fillna("abnormal")
    _derive(out)
    return out


def prepare_unsw(df: pd.DataFrame) -> pd.DataFrame:
    """UNSW-NB15: header row present, includes attack_cat and attempts."""
    out = pd.DataFrame()
    out["duration"] = pd.to_numeric(df.get("dur"), errors="coerce")
    out["packet_count"] = pd.to_numeric(df.get("Spkts"), errors="coerce").fillna(0) + \
        pd.to_numeric(df.get("Dpkts"), errors="coerce").fillna(0)
    out["bytes_sent"] = pd.to_numeric(df.get("Sbytes"), errors="coerce")
    out["bytes_recv"] = pd.to_numeric(df.get("Dbytes"), errors="coerce")
    out["src_port"] = pd.to_numeric(df.get("sport"), errors="coerce")
    out["dst_port"] = pd.to_numeric(df.get("dsport"), errors="coerce")
    proto = df.get("proto")
    out["protocol_encoded"] = proto.map({"tcp": 0, "udp": 1, "icmp": 2}).fillna(3)
    out["is_icmp"] = (proto == "icmp").astype(float)
    raw_label = df.get("attack_cat").fillna(df.get("Label"))
    out["label"] = raw_label.map(UNSW_LABELS).fillna("abnormal")
    _derive(out)
    return out


def _derive(df: pd.DataFrame) -> None:
    df["bytes_sent"] = df["bytes_sent"].fillna(0.0)
    df["bytes_recv"] = df["bytes_recv"].fillna(0.0)
    df["bytes_total"] = df["bytes_sent"] + df["bytes_recv"]
    df["bytes_per_packet"] = df["bytes_total"] / df["packet_count"].replace(0, 1).clip(lower=1)
    df["bytes_ratio"] = df["bytes_recv"] / (df["bytes_sent"] + 1.0)
    df["packets_per_second"] = df["packet_count"] / df["duration"].clip(lower=1e-3)
    df["bytes_per_second"] = df["bytes_total"] / df["duration"].clip(lower=1e-3)
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATURE_COLUMNS[:-1])
    df = df[FEATURE_COLUMNS]
    df["label"] = df["label"].fillna("abnormal")
    return df


_RESPONSIBLE = "For an isolated-lab environment only. Verify you have rights to "
"the dataset. Do not deploy labels/metrics derived from private captures."


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare public datasets for SentinelAI")
    parser.add_argument("--dataset", choices=["cic", "unsw"], required=True)
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--out", type=str, default="datasets/prepared.csv")
    parser.add_argument("--sample", type=int, default=0, help="Keep only N rows (0 = all)")
    args = parser.parse_args()

    print(_RESPONSIBLE)
    raw = pd.read_csv(args.input, low_memory=False)
    out = prepare_cic(raw) if args.dataset == "cic" else prepare_unsw(raw)
    if args.sample > 0:
        out = out.sample(n=min(args.sample, len(out)), random_state=42)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Prepared {len(out)} rows -> {args.out}")
    print(out["label"].value_counts().to_string())


if __name__ == "__main__":
    main()