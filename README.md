# DCIM

Visual data center inventory and control: browse data centers → racks → systems, view simulated
BMC health/power state, and control power at the system (BMC) or outlet (PDU) level. All hardware
access goes through pluggable driver interfaces — simulated for now, real IPMI/Redfish/SNMP later.

## Stack

- Backend: FastAPI + SQLAlchemy (async) + PostgreSQL
- Frontend: React + TypeScript + Vite, SVG rack visualization
- Dev environment: Docker Compose (no local Node/Python version dependency)

## Running locally

```
docker compose up -d postgres
docker compose build backend
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python -m app.seed
docker compose up -d backend frontend
```

- Backend API: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:5173

## Tests

```
docker compose run --rm backend pytest -q
```
