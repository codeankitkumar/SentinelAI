# Dataset & Model Training

## Overview

SentinelAI stores a canonical 13-feature flow vector for every network event.
The same schema is used at training time and at real-time inference so results
are consistent. The feature schema is defined in
`backend/app/ml/__init__.py` (`FEATURE_COLUMNS`).

```
duration, packet_count, bytes_sent, bytes_recv, bytes_total,
bytes_per_packet, bytes_ratio, src_port, dst_port, protocol_encoded,
is_icmp, packets_per_second, bytes_per_second, label
```

Labels (target classes): `normal, port_scan, brute_force, ddos, abnormal`.

## Bundled synthetic dataset (train immediately)

`ml/datasets/sample_netflow.csv` can be generated locally (it is git-ignored
as a large regenerable artifact):

```bash
python ml/generate_sample_data.py --n 6000 --out ml/datasets/sample_netflow.csv
```

It produces labelled, balanced synthetic flows using RFC 5737 TEST-NET IPs —
no real network traffic is involved. This is what `ml/train_model.py` and
`POST /api/ml/retrain` use by default.

## Training & honest metrics

```bash
python ml/train_model.py                        # XGBoost on the sample CSV
python ml/train_model.py --model gradient_boosting

# Retrain via the admin API
curl -X POST http://localhost:8000/api/ml/retrain \
     -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
     -d '{"csv_path": "ml/datasets/sample_netflow.csv", "model_type": "xgboost"}'
```

Artifacts written to:

- `ml/models/sentinel_model.joblib` — classifier
- `ml/models/scaler.joblib` — StandardScaler
- `ml/models/training_report.json` — accuracy / precision / recall / F1 /
  confusion matrix / per-class confidence (computed from a real hold-out split)

The UI displays these numbers under **ML Engine → Training Metrics**. SentisAI
does **not** fabricate detection accuracy — if no model exists it falls back to
a transparent rule-based detector and reports `"mode": "rules"`.

## Using a public research dataset

Supported : **CIC-IDS2017** and **UNSW-NB15**.

`ml/prepare_dataset.py` reduces the raw columns to the canonical feature schema
and maps ground-truth labels into the five SentinelAI classes.

```bash
# CIC-IDS2017 (multi-day labeled capture; ~machine learning friendly)
python ml/prepare_dataset.py --dataset cic \
    --input data/CIC-IDS2017.csv --out ml/datasets/cic_prepared.csv --sample 40000

# UNSW-NB15 (network-based IDS dataset)
python ml/prepare_dataset.py --dataset unsw \
    --input data/UNSW_NB15_training-set.csv --out ml/datasets/unsw_prepared.csv --sample 40000
```

Then train with the prepared file:

```bash
python ml/train_model.py --csv ml/datasets/cic_prepared.csv
```

## Getting the public datasets

- **CIC-IDS2017**: Canadian Institute for Cybersecurity.
  https://www.unb.ca/cic/datasets/ids-2017.html
- **UNSW-NB15**: UNSW Canberra Cyber Range.
  https://research.unsw.edu.au/projects/unsw-nb15-dataset

Licensing/usage: review each dataset's terms. These datasets are intended for
research; use them in an isolated lab and cite the original authors. Do not
deploy models trained on them against live production networks without
additional validation.

## Label mapping summary

| SentinelAI class | CIC-IDS2017 examples | UNSW-NB15 |
|------------------|----------------------|-----------|
| `normal` | Benign | Normal |
| `port_scan` | PortScan, Nmap | Reconnaissance |
| `brute_force` | FTP-Patator, SSH-Patator, Web Attack-Brute Force | Fuzzers |
| `ddos` | DDoS, DoS Hulk/GoldenEye/Slowloris/Slowhttptest, Heartbleed | DoS, Worms |
| `abnormal` | Infiltration, Bot, XSS, SQL Injection, Analysis | Generic, Exploits, Backdoor, Shellcode |

## Notes on performance expectations

Public IDS datasets contain many highly-correlated features; the canonical
13-feature vector trades some expressiveness for a stable, explainable schema
you can reproduce in a live capture pipeline. Report realistic metrics for the
data you actually used — the training script persists whatever it finds on the
hold-out split, and the UI shows exactly that.