# Installation

## Quick start with Docker (recommended)

Prerequisites: **Docker** with the Compose plugin (Docker Desktop on Windows/macOS).

```bash
# from the repo root
cp .env.example .env        # optional; defaults are fine for local
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API (Swagger UI): http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

Demo accounts (created only when `SEED_DEMO_DATA=true`, the default):

```
admin   / Admin@12345      (Administrator)
analyst / Analyst@12345    (Security Analyst)
```

To stop: `docker compose down` (add `-v` to also drop the database volume).

## Run the ML training (optional)

By default a trained model is committed under `ml/models/` so inference works
out of the box. To retrain from scratch with the synthetic dataset:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |  mac/linux: source .venv/bin/activate
pip install -r backend/requirements.txt
python ml/train_model.py                 # uses ml/datasets/sample_netflow.csv
```

The results (accuracy, precision, recall, F1, confusion matrix) are written to
`ml/models/training_report.json` and shown in the UI under **ML Engine**.

Or retrain from the admin UI: **AI Assistant sidebar → ML** via
`POST /api/ml/retrain`.

## Manual local development (no Docker)

### 1. PostgreSQL

Create a database and user, e.g.:

```sql
CREATE USER sentinel WITH PASSWORD 'sentinel_secret';
CREATE DATABASE sentinelai OWNER sentinel;
```

### 2. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | mac/linux: source .venv/bin/activate
pip install -r requirements.txt

# set env so the app reaches your Postgres
#   PowerShell:  $env:DATABASE_URL="postgresql://sentinel:sentinel_secret@localhost:5432/sentinelai"
#   bash:        export DATABASE_URL="postgresql://sentinel:sentinel_secret@localhost:5432/sentinelai"

uvicorn app.main:app --reload --port 8000
```

The first boot creates tables and seeds the demo users/events.

> **SQLite fallback:** if `DATABASE_URL` points to a SQLite file
> (`sqlite:///./sentinel.db`) the app runs without Postgres for a quick test —
> fine for demos, not for production.

### 3. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxies /api to localhost:8000)
```

For an optimized build: `npm run build` (outputs `frontend/dist`).

## Configuration

All settings are environment variables; see `.env.example` for the full list.
Key items:

| Variable | Purpose | Default |
|----------|---------|---------|
| `SECRET_KEY` | JWT signing secret (change in prod) | placeholder |
| `DATABASE_URL` | SQLAlchemy connection string | Postgres via `POSTGRES_*` |
| `SEED_DEMO_DATA` | Seed synthetic events on boot | `true` |
| `NETWORK_MONITOR_ENABLED` | Allow live capture (lab only) | `false` |
| `ASSISTANT_PROVIDER` | `rules` (offline) or `openai` | `rules` |
| `ABUSEIPDB_API_KEY` / `VIRUSTOTAL_API_KEY` | Threat-intel lookups | empty (off) |

## DB schema management

Tables are created automatically via SQLAlchemy `Base.metadata.create_all` on
startup. For production schema migrations, Alembic is included in
`requirements.txt`; initialize with `alembic init` and autogenerate as needed.

## Troubleshooting

- **Backend can't reach Postgres** — ensure the database is running and
  `DATABASE_URL` is correct; with Docker, the backend waits on the `db` health
  check.
- **`docker compose` doesn't start the model** — confirm `ml/models/` exists and
  `ML_MODEL_PATH` points at it (the image bundles it from `ml/models`).
- **Live capture fails** — capture is intentionally disabled unless
  `NETWORK_MONITOR_ENABLED=true` in an authorized lab (see
  [SECURITY_LAB.md](SECURITY_LAB.md)).