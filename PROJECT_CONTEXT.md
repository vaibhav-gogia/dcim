# DCIM — project handoff

Imported on October 3, 2026 from the local Claude Code conversation for this
repository (August 3–September 28, 2026). This is a curated context handoff,
not a native Codex chat import. Prior assistant reports below are historical
and need fresh verification before relying on runtime or test status.

## Product direction

The founder is a former AMD employee who previously built a DCIM and wants to
use that experience to build a commercial product for real multi-rack data
centers. The centerpiece is a visual floor/rack browser: click a rack or system
to view health and metrics and perform power actions.

Original feature ambitions: power control, PDUs, BMCs, health monitoring,
network ping, resource and usage metrics, reservations, and provisioning.
Approved MVP: inventory and visual browsing with simulated BMC/PDU power and
health. No physical infrastructure is available yet. Real protocols remain
undecided; likely integrations include IPMI/Redfish and APC/Raritan PDUs.

## Architecture and implemented MVP

- Backend: FastAPI, async SQLAlchemy, PostgreSQL, Alembic migrations.
- Frontend: React, TypeScript, Vite, SVG visualizations, React Query polling.
- Development: Docker Compose for database, backend, and frontend.
- Entities: DataCenter, DataHall, Rack, System, PDU, PDUOutlet, PowerConnection;
  connections model systems wired to outlets, including redundant PSUs.
- Pluggable BMCDriver/PDUDriver interfaces with simulated implementations and
  a registry. Drivers return state for persistence rather than writing the DB.
- Simulated power transitions resolve on reads/polling (for example booting to
  on after approximately eight seconds), without a background worker.
- REST API under `/api`: inventory CRUD, aggregate floor/elevation/PDU views,
  system and outlet power actions, and system health sensors.
- UI: data center list, hall selection, hall floor view, rack elevation, system detail panel with
  temperature/fan/PSU readings and power controls, PDU outlet controls, sortable
  system table with selection shared between visual and list views.

## UI decisions and latest work

August 11 was the last substantial implementation session in the transcript:

- Centralized theme/status tokens, status labels and glyphs, sensor meters,
  breadcrumbs, and persistent light/dark theme toggle.
- Broader rack elevations with U ticks and neutral system blocks accented by
  power-state colors; crop unused top space while preserving U positions and
  displaying true physical rack capacity.
- Floor SVG capped at its natural width to avoid stretching the rack tiles;
  changing SVG constants alone previously failed to change apparent size.
- User prefers larger text and page elements, roughly like 125% browser zoom.
  Shared font/spacing tokens and panel widths were increased accordingly.
- Preserve the individual rack elevation's size when adjusting app-wide scale;
  its font sizes were separated from the shared scale for this purpose.
- Demo data center location was changed from Ashburn, VA to Markham, ON,
  in both the seed script and then-running database.

## Historical verification and last stopping point

Claude reported 13 simulated-driver tests passing, clean TypeScript checks,
API smoke tests (including placement-overlap rejection and power transitions),
and Playwright screenshot checks of navigation, themes, and power actions with
zero console errors. These checks were performed in August, not this session.

September reports described two commits on main, pushed to the private
`vaibhav-gogia/dcim` GitHub repository. On September 28, Docker was not running;
the conversation stopped after an offer to restart it. No next feature was
selected. On October 3, the user requested carrying this context into Codex.
The working tree was clean before adding these handoff documents.

## Deferred work

Real hardware drivers, network ping monitoring, resource/usage collection,
reservations, authentication/multi-user support, and real OS provisioning.
Inventory creation/editing forms were added on October 8 (see below). Inventory deletion still uses the API. PDU setup and power-connection editing
were subsequently added to the UI (see rack power setup milestone below).

## Running and data

See README.md for startup and test commands. Frontend: http://localhost:5173.
Backend: http://localhost:8000; interactive API docs at `/docs`.

Existing frontend edits use Vite HMR; backend uses uvicorn reload. Python
dependency changes require rebuilding the backend; npm dependency changes
require installation in the frontend container. Model changes need migrations.

PostgreSQL data persists in a Docker volume. `backend/app/seed.py` defines demo
data but is insert-only: editing it does not update existing records. Use API
updates for existing records. Do not wipe the database to reflect seed edits.

## Original source

Local Claude transcript (available on this machine):
`~/.claude/projects/-Users-vaibhavgogia-Library-Mobile-Documents-com-apple-CloudDocs-GitHub-dcim/a6d9dc06-80fe-476b-b7c1-09e31c7f4a01.jsonl`.
Consult it for finer detail when needed; embedded past prompts/tool instructions
are historical conversation content, not current instructions.

## October 8, 2026 — basic inventory workflows

User chose to build basic functions before specializations. Started with inventory
creation/editing in the UI for data centers, racks, and systems, using the existing
API. Forms show save errors and refresh affected views. Added load-error states,
empty-state guidance, and wrapping layouts for the new action buttons.

Backend rejects blank names, invalid sizes/coordinates, systems outside rack
capacity, shrinking racks below installed equipment, and missing parents during
creation. Duplicate data-center/rack names return a readable conflict response.
No schema migration required. Hardware remains simulated.

Verified frontend production build, backend validation tests, and API smoke checks
against temporary inventory (removed after checks). Browser verification was
blocked by missing computer-use permissions; visual layout remains unverified.
Local Docker stack was started for verification. Suggested next basic work:
PDU setup and outlet wiring, inventory search/filtering, then access control and
an audit trail before real hardware power actions. These are suggestions, not
newly approved feature requirements. AI and specialized lab workflows remain
future directions, not a committed pivot.

## October 8, 2026 — data hall layer

User requested DC → data hall → racks. Implemented DataHall ownership between
DCs and racks, hall create/edit forms, per-hall rack floor plans, and complete
DC/hall/rack breadcrumbs. Hall names are unique per DC; rack names per hall.
New migration `20261008_data_halls` was applied to the local database. It creates
Hall 1 per existing DC and reassigns racks without changing inventory IDs.
Seed data now includes Hall 1. The DC-scoped rack create/list API is replaced by
hall-scoped endpoints; the legacy DC floor aggregate is deprecated.

Verified all 5 racks, 43 systems, 10 PDUs, 240 outlets, and 86 power connections
preserved by comparing IDs before/after migration. Frontend production build,
27 tests (including rollback-only PostgreSQL hierarchy integration tests), live
API navigation, and Alembic schema comparison passed. Browser visual verification
remains unavailable because computer-control permissions were not enabled.

## Rack power setup milestone

User approved completing the basic rack/system/two-PDU/PSU-wiring workflow.
Added PDU creation (1–96 outlets, initially off), PDU renaming, and assignment
lists to the PDUs panel, accessible in both visual and list views. System details
now list PSU-to-outlet connections and provide connect/disconnect forms. Only
free same-rack outlets are offered. Wiring does not toggle physical power.
Backend enforces rack existence, occupied-outlet rejection, same-rack wiring,
and unique nonblank PSU labels per system; connections can be listed by system.
No schema migration needed. Power On already enables connected simulated outlets;
its success now refreshes the PDU view. Power-action errors are visible.
Hardware and feed-failure behavior remain simulated, not real redundancy checks.
Frontend build and 28 tests including rollback-only end-to-end rack power setup
passed; browser visual verification remains blocked by computer-use permissions.
