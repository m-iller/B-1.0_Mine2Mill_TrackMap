# MOMPS prototype

Offline-first modular monolith (FastAPI) + React dashboard + PostgreSQL/PostGIS + InfluxDB + RabbitMQ.

## Prerequisites

- Docker (Postgres+PostGIS, InfluxDB 2, RabbitMQ)
- Python 3.11+
- Node 20+ (frontend)

## 1. Data stores

```bash
cd momps
docker compose up -d
```

Copy `backend/.env.example` to `backend/.env` and adjust secrets for non-dev use.

## 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET http://127.0.0.1:8000/health`
- Login: `POST /api/v1/auth/login` body `{"username":"operator","password":"demo"}` (override via `MOMPS_DEMO_*` env)
- Use `Authorization: Bearer <token>` on protected routes.

## 3. Synthetic dataset

```bash
python scripts/generate_synthetic_dataset.py
```

Writes `data/example_training.csv`.

## 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`, login, map + WebSocket stream from backend `:8000`.

## 5. Example API

See `examples/api.http`.

## Modules (backend `app/`)

| Area | Path |
|------|------|
| Telemetry ingest + Influx | `services/telemetry_ingestion.py`, `influx_writer.py` |
| Simulation + terrain | `services/simulation_engine.py` |
| Routing A* + JIT | `services/routing_engine.py` |
| Safety | `services/safety_system.py` |
| Planning | `services/planning_engine.py` |
| ML (sklearn) | `ml/pipeline.py` |
| PDF | `services/reporting_service.py` |
| Broker abstraction | `broker/` |
| Mesh / LoRa mock | `networking/mesh_lora.py` |
| Extension hooks | `extensions/hooks.py` |

Schema version: `db/init/001_schema_v1.sql` (`schema_migrations` table).

## Notes

- Broker connection failure on startup is non-fatal (offline-first).
- WebSocket clients should send occasional ping (dashboard does every 20s).
- For production: replace demo auth, wire Alembic migrations, add Kafka backend, scale workers with shared sim state (Redis/DB).
