# SentinelAI — AI-Powered Cyber Threat Detection & SOC Platform

> **Important:** SentinelAI is designed for **authorized environments and isolated
> lab use only** (e.g., your own captured traffic, publicly released datasets
> such as CIC-IDS2017 / UNSW-NB15, or the included synthetic generator). Live
> network capture requires explicit authorization. See
> [docs/SECURITY_LAB.md](docs/SECURITY_LAB.md).

SentinelAI is a modular Security Operations Center (SOC) platform that:

- Monitors (authorized) network traffic and extracts network features.
- Detects port scans, brute-force patterns, DDoS indicators, and abnormal flows.
- Trains ML models (Scikit-learn + XGBoost) for threat classification and runs
  real-time inference.
- Provides an interactive SOC dashboard, alert triage, incident management
  (with PDF export), a rule- or LLM-backed AI assistant, and optional threat
  intelligence lookups (AbuseIPDB / VirusTotal).

## Features

- **Authentication & RBAC** — JWT login, bcrypt hashing, `admin` / `analyst`
  roles with enforced endpoint authorization and admin user management.
- **Security monitoring engine** — authorized flow aggregation, feature
  extraction and explainable detection rules for port scans, brute-force,
  DDoS indicators, and abnormal traffic (Scapy capture guarded by
  `NETWORK_MONITOR_ENABLED`; disabled by default).
- **AI threat detection** — Scikit-learn + XGBoost classification with real
  (non-fabricated) metrics: precision, recall, F1, confusion matrix, persisted
  to `ml/models/training_report.json` and surfaced in the UI.
- **SOC dashboard** — total events, critical incidents, active alerts, attack
  distribution, network activity over time, top suspicious IPs, recent alerts.
- **Incident management** — triage alerts, assign severity, add investigation
  notes, change status, and **export incident reports as PDF**.
- **AI assistant** — explain, summarize, investigate, remediate, and generate
  incident reports; offline rule-based by default, with optional OpenAI backing.
- **Threat intelligence** — AbuseIPDB / VirusTotal reputation lookups that
  respect rate limits (disabled until API keys are configured).
- **Threat modeling data** — synthetic generator + `prepare_dataset.py` for
  public CIC-IDS2017 / UNSW-NB15 datasets.

## Tech Stack

| Layer     | Technology                                             |
|-----------|--------------------------------------------------------|
| Frontend  | React 18, Vite, Tailwind CSS, Recharts, Axios          |
| Backend   | Python 3.12, FastAPI, SQLAlchemy 2, Alembic            |
| Database  | PostgreSQL 16                                          |
| ML        | Scikit-learn, XGBoost, pandas, Jupyter                 |
| Capture   | Scapy (authorized lab only)                            |
| Deploy    | Docker, docker-compose                                 |

## Quick Start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- Backend API: http://localhost:8000 (Swagger: http://localhost:8000/docs)
- Frontend:   http://localhost:5173

Default demo credentials (created only when `SEED_DEMO_DATA=true`):

```
admin / Admin@12345    (Administrator)
analyst / Analyst@12345 (Security Analyst)
```

## Repo Layout

```
backend/        FastAPI app (API routers, models, monitor, ML, assistant)
frontend/       React + Tailwind SPA
ml/             ML training scripts, dataset generation/preparation, models
docs/           API reference, install, lab safety, dataset prep
docker-compose.yml     Postgres + backend + nginx frontend
.env.example           environment template (copy to .env)
```

## Documentation

| Document | What it covers |
|----------|----------------|
| [docs/INSTALL.md](docs/INSTALL.md) | Docker + manual install, config reference |
| [docs/API.md](docs/API.md) | Full REST endpoint reference & role matrix |
| [docs/DATASETS.md](docs/DATASETS.md) | Feature schema, training, public dataset prep |
| [docs/SECURITY_LAB.md](docs/SECURITY_LAB.md) | Authorized-lab & capture guardrails |

## Deliverables map

Complete source code · database schema (SQLAlchemy models, auto-created on
startup) · API docs · ML training scripts + sample dataset generator · sample
dataset instructions · Docker configuration · environment template
(`.env.example`) · this README with installation instructions.

> **Live capture** is disabled by default and is only for authorized lab
> environments — see [docs/SECURITY_LAB.md](docs/SECURITY_LAB.md) before
> enabling.