# DCIM

Visual data center inventory and control: browse data centers → data halls → racks → systems, view simulated
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

## Managing inventory

Use **Add data center** on the home page, **Add data hall** inside a data center,
**Add rack** inside a data hall, and **Add system** inside a rack. Each page also offers editing; select a system
in the visual or list view to reveal **Edit selected system**. Rack positions use
floor column/row coordinates; system positions start at U1 at the bottom.
Systems must fit within rack capacity and cannot overlap existing systems.

Power and health remain simulated. PDU setup, power connections, and deletion
are currently available through the API docs rather than these forms.

## Data halls

The hierarchy is **Data center → Data hall → Rack → System**. Each hall has its
own rack floor plan. Hall names are unique within a data center; rack names are
unique within a hall. Breadcrumbs let you return from a rack to its hall or DC.

After pulling this change, run `docker compose exec backend alembic upgrade head`
before using the app. Existing data centers receive a **Hall 1**, containing their
existing racks. Rack IDs, equipment, outlet wiring, and power states are preserved.
Fresh demo seeds also create Hall 1. Do not re-seed an existing database.

API: create/list halls at `/api/datacenters/{id}/data-halls`; read/edit/delete a
hall at `/api/data-halls/{id}`; floor plan at `/api/data-halls/{id}/floor`;
create/list racks at `/api/data-halls/{id}/racks`. The former DC-scoped rack
creation/list endpoints are replaced by these hall-scoped endpoints. Rack reads
now contain `data_hall_id` rather than `datacenter_id`. The old DC floor endpoint
is deprecated and returns a cross-hall aggregate, not a hall layout.

Run database-backed hierarchy tests after migrations:

```bash
docker compose exec -e RUN_DB_TESTS=1 backend pytest -q
```

These integration tests roll back their changes and preserve existing inventory.
