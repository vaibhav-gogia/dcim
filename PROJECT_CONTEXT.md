# DCIM — project handoff

Imported on October 3, 2026 from the local Claude Code conversation for this
repository (August 3–September 28, 2026). This is a curated context handoff,
not a native Codex chat import. Prior assistant reports below are historical
and need fresh verification before relying on runtime or test status.

## Current checkpoint — October 27, 2026

Login, API-enforced viewer/operator/admin roles, account management, persistent
action history, and disruptive-power confirmations have been implemented after
user approval. Migration `20261027_accounts_audit` was applied locally. There are
no default credentials. First-admin creation uses the interactive command in
`docs/ACCOUNTS_AND_HISTORY.md`; do not assume the user has completed it.

Last implementation verification: 41 tests passed, frontend build passed, and
Alembic schema comparison matched. Browser inspection confirmed the sign-in/setup
screen. The signed-in multi-role workflow remains unverified. This documentation
update did not rerun runtime tests. Next step is that walkthrough, then fixing
any defects before starting the proposed hardware pilot. User asked to pause
feature work and finish documentation; do not infer approval for another feature.

Current references: `docs/PRODUCT_PLAN.md` for scope,
`docs/ACCOUNTS_AND_HISTORY.md` for setup/permissions/history, and `README.md` for
startup and development. The timeline below includes superseded historical states.

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
reservations, enterprise identity/SSO/MFA, and real OS provisioning. Local
authentication and roles were subsequently implemented; see the current checkpoint.
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

## Inventory search and filtering

Added a global Search inventory navigation link and `/inventory` page. Backend
system search joins rack/hall/DC context, supports literal case-insensitive text
search, combined location/manufacturer/type/power filters, and bounded pagination.
UI stores filters/search/page in the URL, refreshes results every five seconds,
and links to `/rack/{id}?system={id}` to open the system detail panel directly.
Rack selection now follows that URL parameter. Simulated transition states are
computed at search time using the driver's transition-duration constants, so
completed booting/cycling/shutdown states do not remain stale in filters.
No schema migration. Search returns systems, not standalone PDU/rack matches.
Validation includes PostgreSQL integration tests for serial-number wildcard
escaping, combined filters, parent context, pagination, and completed transitions.

## Product documentation pause

User requested a mission statement, Day 1 scope, and later roadmap to preserve
focus. Created `docs/PRODUCT_PLAN.md` and linked it from README and AGENTS.md.
It distinguishes the current simulated foundation demo from a proposed Day 1
customer pilot, records implemented versus missing features, and keeps lab/AI
specializations as unvalidated options. Recommended next implementation is
accountable operations: users, API-enforced permissions, action history, and
power-action safeguards, after a foundation browser walkthrough. These are
recommendations for review; no new implementation was authorized by this pause.

## October 27, 2026 — PDU supply-loss correction

User reported systems staying online after all connected outlets were switched
off. Simulated outlet changes now reconcile attached system state: the last feed
going off immediately persists OFF and cancels pending transitions. A remaining
powered feed preserves operation. AC restoration leaves the system off until
Power On; existing Power On behavior still enables connected outlets. BMC cycling
without a powered feed returns a conflict. Outlet cycling models the interruption
before restoring AC. Wired PSU health reports actual connected outlet input.
Read paths and inventory power filters also honor loss of all wired inputs;
unwired demo systems keep standalone behavior. Frontend outlet actions immediately
invalidate system health/detail and inventory queries. No schema change.
Regression tests cover running/booting systems, single/dual feeds, zero fans,
restoration, outlet cycling, and consistent search/elevation/detail states.

## October 27, 2026 — separate BMC and PDU controls

User requested correcting System Power On automatically enabling PDU outlets.
Removed that behavior: wired simulated systems with no live feed return HTTP 409
with instructions to turn on a connected outlet. One live feed permits booting
without enabling other outlets. Unwired systems retain standalone demo behavior.
BMC cycle errors use the same guidance. This supersedes the earlier notes about
Power On enabling outlets. Tests now explicitly power outlets before booting and
assert rejected/degraded Power On requests do not modify outlet states.

## October 27, 2026 — hall layout editing and rack deletion

User approved implementing within-hall dragging and a rack deletion UI. Data hall
pages now offer Edit layout with draft positions, pointer dragging, keyboard arrow
movement, 0.1-cell snapping, overlap warnings, and Save/Cancel. An atomic backend
layout endpoint validates membership, original coordinates (stale edit detection),
and tile overlap before saving all rack positions. Rack deletion displays counts
of systems/PDUs/outlets/connections and requires typing the exact rack name.
Successful deletion returns to the hall and refreshes inventory. Moving racks
between halls remains deferred. No schema migration required. Browser visual
verification remains outstanding; frontend build and database regression tests
cover compilation, layout validation/atomicity, and inventory deletion cascades.

## October 27, 2026 — accountable operations and completed documentation

Implemented local accounts and opaque, revocable cookie sessions. Passwords use
salted scrypt; raw session/CSRF tokens are not stored in the DB. Sessions expire
after eight hours by default. Account changes revoke sessions; five failed logins
trigger a five-minute account lock. No default users were created by migration.
Bootstrap is local and refuses when accounts already exist. Admin UI supports
create/role/active/password changes and protects the last active administrator.

All inventory APIs now require authentication. Viewer reads; operator additionally
controls system/outlet power; admin manages inventory, wiring, layouts, and users.
Frontend controls follow roles. Power off/cycle requests require confirmation.
Action history is accessible globally and by rack/system. Audit intent is recorded
before a mutation and completion afterward in a separate transaction. Pending
simulated power transitions can settle on reads; unknown outcomes are not reported
as success. Records survive target deletion and omit passwords/raw inventory field
values. This is not a tamper-proof audit system. Hall layout events are associated
with the hall and appear globally, not in each rack's filtered history.

Migration adds users/login_sessions/audit_events without replacing inventory.
FastAPI minimum is now 0.121 for function-scoped DB dependencies. Integration
fixtures now use unique temporary schemas with independent sessions instead of
shared rollback transactions, so audit transactions match production behavior.
All 41 tests passed in the last full run. Settings for secure cookies, session
hours, and allowed origins are wired through Compose and `.env.example`.

Completed docs: account guide, README startup/test corrections, current permission
matrix, history semantics, configuration, limitations, and remaining browser
acceptance checklist. Real account creation status is unknown; the user was given
the interactive bootstrap command and must enter their password privately.

## October 28, 2026 — login and account UI refinements

Added a Show/Hide password control to login (hidden by default and on submission).
Header tools now use consistent icon links and a compact account dropdown for
settings/sign-out. Account forms use shared padding, stacked labels, responsive
fields, and separate action rows. Admin user management now presents a searchable
user table with role/status filters, self-account marking, Add user, and a single
selected Edit form with Save/Cancel. Existing role, activation, password-reset,
session-revocation, and last-admin protections are unchanged. Frontend production
build passed after these changes; no new backend behavior was introduced.

User reported Edit appearing to do nothing. The form previously rendered above
the user list, potentially outside the viewport. Editing now expands directly
beneath the selected row and focuses/scrolls its heading into view. Add user
remains above the list. Frontend production build passed.
