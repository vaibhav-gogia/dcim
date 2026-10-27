# DCIM product plan

Last updated: October 8, 2026.

This is the working product plan. It captures agreed direction and proposes a
launch boundary for review. The current inventory-first direction is agreed;
the Day 1 release criteria and later sequencing below are recommendations,
not evidence that those features are already implemented or customer-validated.

## Mission

**Help infrastructure teams understand, find, and safely operate their physical
systems from one clear view of their data centers.**

We are building toward a commercial DCIM product for multi-rack environments,
drawing on the founder's experience building DCIM at AMD. The foundation is
accurate inventory, visible physical relationships, and trustworthy operational
controls. Specialized workflows and AI should build on that foundation.

## Who we are building for

Initial users: infrastructure operators and engineers who manage physical
servers, racks, and PDUs across data centers and data halls.

Their core questions:

- Where is this system, and what hardware is it?
- What is its current health and power state?
- Which outlets supply its PSUs?
- Can I operate it safely, and see what happened afterward?

The initial buyer, budget, hardware mix, and willingness to pay still need
validation. Shared semiconductor/hardware labs are a promising segment to
investigate because of the founder's experience. We have not committed to
pivoting away from general DCIM or making reservations the primary product.

## What Day 1 means

Separate two milestones so a polished simulator is not mistaken for a
customer-ready hardware product:

1. **Foundation demo:** a complete inventory and simulated operations workflow.
   This is the current development target and is substantially implemented.
2. **Day 1 customer pilot:** a small team uses that workflow on a deliberately
   limited, documented hardware configuration with access control and traceable
   actions. This is the proposed first external release, not broad vendor support.

Success scenario: an operator creates a DC and hall, adds a rack and system,
sets up two PDUs, connects the PSUs, finds the system through search, performs an
authorized power action, and sees its outcome and history.

## Day 1 scope and current status

| Capability | Current status | Proposed pilot requirement |
| --- | --- | --- |
| DC → hall → rack → system hierarchy | Implemented | Preserve relationships and equipment IDs through upgrades |
| Inventory creation and editing | Implemented; PDU editing currently renames only | Complete routine setup through the UI; keep outlet count fixed for this release |
| Floor/rack views and system detail | Implemented | Verify layouts and navigation in a real browser |
| Search and filtering | Implemented for systems with location context | Find by name/serial/model and combine location/type/manufacturer/state filters |
| PSU-to-outlet wiring | Implemented, same-rack only | Show assignments; reject occupied outlets and duplicate PSU labels |
| System and outlet power controls | Simulated | Support one agreed pilot hardware configuration and report failures honestly |
| Temperature, fan, and PSU health | Simulated snapshots | Timestamp real readings and make stale or failed collection visible |
| Users and permissions | Not implemented | Viewer, operator, and administrator roles; enforce permissions in the API |
| Action history | Not implemented | Record actor, target, time, action, and outcome for inventory/wiring/power changes |
| Power-action safeguards | Partial: disabled transient-state buttons and visible API errors | Confirm disruptive actions; track pending/succeeded/failed/unknown outcomes without blind retries |
| Inventory onboarding | Manual UI/API | Prove the pilot's onboarding is manageable; add CSV import if manual entry blocks it |
| Deployment and recovery | Docker dev setup and migrations | Document installation, configuration, credentials, backup and restore; verify recovery |

“Implemented” describes current code, not production readiness. Latest development
checks reported a passing frontend build and 29 backend tests, including
PostgreSQL integration tests. Recent browser verification remains outstanding
because computer-use permissions were unavailable. Recheck before release.

## Explicitly outside Day 1

- Broad support for BMC/PDU vendors and protocols.
- Reservations, shared-lab scheduling, and allocation workflows.
- OS provisioning, imaging, and automated configuration management.
- Deep CPU/GPU/memory utilization and workload analytics.
- Capacity forecasting, placement optimization, and electrical/cooling planning.
- AI diagnosis, predictive maintenance, and autonomous remediation.
- Elaborate 3D floor plans, drag-and-drop layout editing, and advanced reporting.
- Full network/IP address management and replacement of existing customer tools.
- Billing, a multi-tenant SaaS control plane, and enterprise integration breadth.

Rack deletion with typed confirmation and a contents summary, plus within-hall
layout editing with Save/Cancel, were subsequently approved and implemented.
Deletion of other inventory types, moving racks between halls, and bulk operations
remain backlog candidates. Do not expand Day 1
for these unless a pilot workflow requires them.

## Logical next milestone: accountable operations

**Recommended next implementation: users, permissions, and an action history.**
The inventory/setup/search loop now exists. The next gap is knowing who can
change equipment and who performed an operational action.

Acceptance criteria:

- A viewer can browse/search but cannot change inventory, wiring, or power.
- An operator can run permitted operational actions; an administrator manages
  users and inventory. Define the exact permission matrix before implementation.
- API calls enforce permissions even when the UI is bypassed.
- Changes and power requests produce history entries with actor, target, time,
  and outcome; failed actions are visible too.
- Operators confirm power-off, cycling, and other disruptive actions.
- Action status distinguishes a confirmed failure from an unknown hardware
  outcome; the system does not silently retry a potentially completed action.
- Tests cover role boundaries and history recording, followed by a browser pass.

Do not start new feature implementation as part of this documentation pause.
Authentication approach and the permission matrix remain implementation decisions
to settle before this milestone begins.

## Sequence after accountable operations

| Stage | Deliverable | Exit condition |
| --- | --- | --- |
| 1. Confirm foundation | Browser walkthrough and fixes for setup/search/wiring flows | The complete demo scenario works without manual API intervention |
| 2. Accountable operations | Permissions, audit history, and action safeguards | The acceptance criteria above pass |
| 3. Hardware pilot | One customer-selected BMC/PDU configuration, reachability, timestamps, and collection failures | Demonstrate real reads/actions and failure handling on representative equipment |
| 4. Pilot readiness | Installation, onboarding, backup/restore, and operator instructions | A pilot operator can use and recover the installation with documented support |
| 5. Specialization | One validated customer workflow | A customer identifies the problem, success measure, and willingness to pay |

Customer interviews and securing access to representative hardware should proceed
alongside foundation work. Vendor selection depends on that access; no protocol
or commercial launch date is committed yet.

## Later opportunities

- **Shared lab operations:** reservations, ownership, allocation expiry, and
  measured utilization. Validate whether engineering teams need this first.
- **Operational monitoring:** reachability history, thresholds, alerts, and
  incident workflows once reliable collection exists.
- **AI investigation:** evidence-backed explanations and operator-approved
  recovery steps, after telemetry, event history, permissions, and audit exist.
- **Capacity planning:** deterministic space/power/redundancy constraints first;
  forecasts and AI explanations only when inputs and assumptions are trustworthy.
- **Provisioning:** integrate existing automation before building a complete
  imaging/provisioning platform.

These are options, not promises. Choose the first specialization from pilot
experience rather than implementing all of them.

## How we keep scope under control

Before adding a feature, identify its user, concrete problem, measurable outcome,
and whether it is required for the current milestone. If it does not complete
the milestone or remove a pilot blocker, record it for later.

Update this document when the target user, release scope, or milestone changes.
Keep implementation history in [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md) and
setup/usage instructions in [README.md](../README.md). Review this plan at each
milestone boundary; do not promote brainstormed ideas to committed scope silently.
