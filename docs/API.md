# SentinelAI API Reference

Base URL (development): `http://localhost:8000/api`

All endpoints except `/auth/login` require a bearer token header:

```
Authorization: Bearer <access_token>
```

An interactive spec is available at `http://localhost:8000/docs` (Swagger UI)
and `http://localhost:8000/redoc`.

## Authentication

| Method & path | Auth | Description |
|---------------|------|-------------|
| `POST /auth/register` | – | Create an analyst account. Returns a token. |
| `POST /auth/login` | – | `{username, password}` → JWT token. |
| `GET /auth/me` | any user | Current user profile. |
| `GET /auth/users` | admin | List all users. |
| `POST /auth/users` | admin | Create a user (any role). |
| `PATCH /auth/users/{id}` | admin | Update a user (role, password, active). |

Login request:

```json
{ "username": "admin", "password": "Admin@12345" }
```

Login/token response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "username": "admin",
  "role": "admin",
  "user_id": 1
}
```

## Security monitoring

| Method & path | Auth | Description |
|---------------|------|-------------|
| `GET /events` | analyst | Paginated flow events with filters. |
| `GET /events/{id}` | analyst | One network event. |
| `GET /alerts` | analyst | Paginated alerts with filters. |
| `GET /alerts/{id}` | analyst | One alert. |
| `PATCH /alerts/{id}` | analyst | Update status/severity (triage). |

`GET /events` query params: `query`, `threat_type`, `severity`, `start`, `end`,
`page`, `page_size` (max 200).

`GET /alerts` query params: `query`, `severity`, `status`, `source_ip`,
`start`, `end`, `page`, `page_size`.

List responses are shaped as `{ total, page, page_size, items: [...] }`.

## SOC dashboard

| Method & path | Auth | Description |
|---------------|------|-------------|
| `GET /dashboard/stats` | analyst | Aggregated dashboard (stat cards, charts, top IPs, recent items). |

## Incident management

| Method & path | Auth | Description |
|---------------|------|-------------|
| `GET /incidents` | analyst | Paginated incidents. |
| `POST /incidents` | analyst | Create incident (optionally with `alert_ids`). |
| `GET /incidents/{id}` | analyst | Incident detail incl. notes. |
| `PATCH /incidents/{id}` | analyst | Update status/severity/assignee/alerts. |
| `POST /incidents/{id}/notes` | analyst | Add an investigation note. |
| `GET /incidents/{id}/export` | analyst | Download an incident report as **PDF**. |

## AI assistant

| Method & path | Auth | Description |
|---------------|------|-------------|
| `POST /assistant/query` | analyst | Get guidance. |

Request:

```json
{
  "intent": "investigate",           // explain | summarize | investigate | remediate | report
  "query": "why did this trig alerts",
  "alert_id": 12,                    // optional
  "incident_id": 3,                  // optional
  "source_ip": "203.0.113.7"         // optional
}
```

Response: `{ "intent", "answer", "steps": [], "sources": [] }`.
Provider is `rules` (offline) by default; set `ASSISTANT_PROVIDER=openai`
(when `OPENAI_API_KEY` is set) to use an LLM for explain/investigate/remediate.

## Threat intelligence

| Method & path | Auth | Description |
|---------------|------|-------------|
| `GET /threatintel/providers` | analyst | Which providers are configured. |
| `GET /threatintel/lookup/{ip}` | analyst | Reputation lookup (AbuseIPDB/VirusTotal). |

Lookup returns a list of `ThreatIntelResult` objects:
`{ ip, provider, found, data, note, queried_at }`.
Disabled providers return a clear "not configured" note rather than failing.

## ML engine

| Method & path | Auth | Description |
|---------------|------|-------------|
| `GET /ml/status` | analyst | Inference mode (`trained`/`rules`) + training report metrics. |
| `POST /ml/retrain` | admin | Retrain on `ml/datasets/sample_netflow.csv` (or `csv_path`). |

## Network monitor

| Method & path | Auth | Description |
|---------------|------|-------------|
| `GET /monitor/capture` | analyst | Capture enabled/available + interface. |
| `POST /monitor/capture/start` | admin | Validate & start capture (lab only). |
| `POST /monitor/simulate` | admin | Ingest one synthetic flow (never real traffic). |
| `GET /monitor/summary` | analyst | Event counts + monitor flag. |

## Errors

Errors use FastAPI's standard shape: `{ "detail": "message" }`.

- `401` – missing/invalid token
- `403` – authenticated but insufficient role
- `404` – resource not found
- `422` – validation error (field-level details)

## Role matrix

| Endpoint group | analyst | admin |
|----------------|:-----:|:---:|
| Auth (register/login/me) | ✔ | ✔ |
| User management | – | ✔ |
| Events / Alerts / Dashboard / Incidents | ✔ | ✔ |
| AI assistant / Threat intel | ✔ | ✔ |
| ML status | ✔ | ✔ |
| ML retrain | – | ✔ |
| Monitor simulate / capture start | – | ✔ |

## Notes

- **Accuracy is not fabricated.** The `GET /ml/status` metrics come from the
  model actually evaluated on the held-out split of the labeled dataset; see
  `ml/models/training_report.json`.
- Live capture requires `NETWORK_MONITOR_ENABLED=true` in an authorized lab
  (see [SECURITY_LAB.md](SECURITY_LAB.md)).