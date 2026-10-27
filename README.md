# DCIM

Visual data center inventory and control: browse data centers → data halls → racks → systems, view simulated
BMC health/power state, and control power at the system (BMC) or outlet (PDU) level. All hardware
access goes through pluggable driver interfaces — simulated for now, real IPMI/Redfish/SNMP later.

## Product direction

See [the product plan](docs/PRODUCT_PLAN.md) for the mission, proposed Day 1
scope, current gaps, and later opportunities.

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

Power and health remain simulated. Racks can be deleted from their page with
a typed confirmation; other inventory deletion remains available through the API.

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

## Rack power setup

1. Open a rack and add a system.
2. In the PDUs panel, choose **Add PDU** to create PDU A and PDU B, each with
   1–96 outlets. New outlets start off. **Edit PDU** renames a PDU; outlet count
   is fixed after creation.
3. Select the system in the rack or list view. Under **Power connections**, enter
   PSU1 and select an outlet on PDU A, then connect PSU2 to an outlet on PDU B.
4. Turn on at least one connected PDU outlet, then use **Power On**. The system
   enters booting, then on as polling resolves the transition. Power Off and Power Cycle
   remain available, and outlet buttons toggle individual outlets.

Only unassigned outlets in the same rack are offered. The API also rejects
occupied outlets and duplicate PSU labels on a system. **Disconnect** removes the
inventory connection without changing outlet power. A/B labels document wiring;
the simulator models loss of connected outlet power, but not upstream circuits,
UPS capacity, or electrical redundancy limits.

## Inventory search

Choose **Search inventory** in the navigation bar. Search systems across all
sites by name, serial number, manufacturer/model, rack, hall, DC name, or DC
location. Combine data-center, data-hall, manufacturer, system-type, and
power-state filters. Results are paginated (25 per page) and refresh every five
seconds. Search/filter state is stored in the URL for sharing and browser history.
Click a system name to open its rack with that system's detail panel selected.

API: `GET /api/inventory/systems` accepts `q`, `datacenter_id`, `data_hall_id`,
`manufacturer`, `system_type`, `power_state`, `offset`, and `limit` (1–100).
Filters combine with AND; text search is case-insensitive and treats wildcard
characters literally. `GET /api/inventory/filters` supplies filter options.
Simulated power transitions are evaluated at query time; search does not poll
physical equipment. Inventory search currently returns systems, with their
parent locations, rather than separate PDU/rack result types.

### Simulated loss of PDU power

A wired simulated system stays powered while at least one connected outlet is on.
Turning off its last powered outlet immediately sets the system off, cancels any
boot/cycle transition, stops fans, and reports no input on the affected PSUs.
Restoring outlet power does not automatically boot the system; use Power On.
System Power On never changes outlet power. If every connected outlet is off,
it rejects the request with guidance to turn on a PDU outlet first. One powered
feed is enough to boot; any other outlets remain unchanged.
Cycling the only powered feed interrupts the system; cycling a redundant feed does
not. Unwired demo systems retain standalone simulated BMC behavior because their
power source is unknown. Wiring edits describe inventory and do not toggle relays.

## Editing hall layouts and deleting racks

On a data hall page, select **Edit layout**. Drag racks into place, or focus a
rack and use arrow keys to move it by 0.1 cell. **Save layout** persists all
positions together; **Cancel** discards the draft. Rack tiles cannot overlap.
If another user changes rack membership or positions during editing, saving is
rejected with instructions to cancel and reload. Layout editing changes positions
within the current hall; moving racks between halls is not included.

On a rack page, choose **Delete rack**. Review the counts of systems, PDUs,
outlets, and power connections, then type the rack's exact name and confirm.
This permanently deletes those inventory records and returns to the hall.
It does not issue power commands to physical equipment.
