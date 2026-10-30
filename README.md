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
backend/        FastAPI application (API, models, monitor, ML, assistant)
frontend/       React + Tailwind SPA
ml/             ML training scripts, feature engineering, dataset prep
docs/           API docs, lab setup, dataset preparation
docker-compose.yml
.env.example
```

See [docs/INSTALL.md](docs/INSTALL.md) for manual/local installation,
[README full](#deliverables) for the deliverable map, and each section below.

> **Remote GitHub:** this repo commits locally. To push to a remote, add your
> repository: `git remote add origin <url>` then `git push -u origin main`.