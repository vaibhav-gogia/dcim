# Accounts, permissions, and action history

Updated October 27, 2026. This describes the implemented local-account milestone.
Hardware control and health readings remain simulated; this is not a production
security certification.

## First administrator

From the project root, with Docker running:

```bash
docker compose up -d postgres
docker compose build backend
docker compose run --rm backend alembic upgrade head
docker compose up -d backend frontend
docker compose exec backend python -m app.bootstrap_admin
```

The interactive command asks for a username and a password twice. Password input
is hidden. There are no default credentials, and the command refuses to create an
initial administrator when any accounts already exist. It does not change inventory.

- Usernames: 3–64 lowercase letters/digits, with dots, hyphens, or underscores;
  the first character must be a letter or digit. The setup command lowercases input.
- Passwords: 12–128 characters. Use a unique password and save it in your password
  manager; do not put it in source control, shell arguments, or chat.
- Open http://localhost:5173 and sign in. Use the same hostname consistently;
  `localhost` and `127.0.0.1` have separate browser cookies.
- Existing installations use the same migration commands. Do not re-seed the
  database or rerun bootstrap to reset an existing account.

Migration `20261027_accounts_audit` adds `users`, `login_sessions`, and
`audit_events`. It preserves existing inventory and creates no accounts.

## Permissions

These roles apply across the installation, not separately by DC or hall.

| Capability | Viewer | Operator | Admin |
| --- | --- | --- | --- |
| Browse inventory, health, floor plans, and system search | Yes | Yes | Yes |
| Read global/rack/system action history | Yes | Yes | Yes |
| System power on/off/cycle and PDU outlet power control | No | Yes | Yes |
| Add/edit/delete inventory; edit layouts and PSU wiring | No | No | Yes |
| List/create/update/disable users and reset their passwords | No | No | Yes |
| Change own password and sign out | Yes | Yes | Yes |

The frontend hides or disables unavailable controls. The API independently
checks every protected request, so bypassing the UI does not bypass permissions.
Unauthenticated requests receive HTTP 401; role and CSRF denials receive HTTP 403.
The public endpoints are sign-in, setup-status, and the basic `/api/ping` probe.
The API schema/documentation pages remain accessible without signing in; protected
operations still require a valid session.

## Account management

Click your username/role in the navigation to open **Account**. Administrators
see a user table with usernames, roles, and active/disabled status. Search by
username or filter by role/status. Use **Add user** to create an account and
**Edit** beside a user to change roles, disable/reactivate access, or reset a
password. The selected editor expands directly beneath its user row, scrolls into view,
and receives keyboard focus. Save and Cancel controls stay with that editor.
Accounts are disabled rather than deleted, and the API prevents disabling or
demoting the last active administrator.

Updating an account revokes all its current sessions. Changing your own password
also revokes all your sessions and requires signing in again. Signing out revokes
the current session only. There is no email-based password recovery, public
registration, SSO, or MFA in this milestone. Ask another administrator for a reset;
if all administrator credentials are lost, there is not yet a dedicated recovery
command. Do not delete account tables or inventory to bypass account setup.

Five failed sign-in attempts lock that account for five minutes. Further attempts
while locked extend the lock. Successful sign-in after the lock expires resets
the failure counter. This is account-level throttling, not an IP/global rate limiter.

## Disruptive power actions

The UI asks for confirmation before system power-off/cycle and before turning off
a PDU outlet. Outlet warnings name the connected system when one is recorded.
Canceling the confirmation sends no action request. The system's existing typed
rack-deletion confirmation is separate and does not issue hardware power commands.

The API requires `X-Confirm-Action: yes` for power-off and cycle endpoints. This
header records the client's confirmation intent; it does not replace authentication
or authorization and cannot prove that a human actually saw a dialog.

## Reading action history

Use **Activity** in the navigation for the full log. Rack pages and system details
also show history filtered to records associated with that rack/system. Hall-wide
layout saves are recorded against the hall and appear in the global log.

Records include actor, time, method/route, target identity/name, changed field
names, HTTP status where available, and outcome. Deletion does not delete the
corresponding history. Inventory field values and passwords are not recorded.
Sign-ins and rejected sign-in attempts with valid input are also recorded.
Protected mutation attempts by authenticated users are logged, including permission,
validation, and power-supply rejections. Ordinary reads and unauthenticated
inventory requests are not recorded as action events.

| Outcome | Meaning |
| --- | --- |
| `pending` | Request started, or a power command was accepted and its final state has not been observed |
| `succeeded` | Request completed; for a transitional power command, the system reached its expected state |
| `failed` | Request was rejected, or a pending transition was observed to fail/interrupted |
| `unknown` | A server/driver failure prevented confirmation, or no completion was observed for over five minutes |

Check equipment and history before retrying an unknown action. The application
does not automatically retry power mutations. Simulated transitions can settle
when health/power/rack state or relevant history is read. A five-minute unknown
status is a presentation of missing confirmation, not proof that equipment failed.

A pending record is committed before a protected mutation executes. Completion is
written afterward in a separate transaction. If execution or final bookkeeping
fails, the earlier record can remain unresolved. This is not one atomic transaction
covering both external hardware and the database. There is no history-deletion API,
but database administrators can modify the database; this is not a tamper-proof or
compliance-certified audit store. Logging before this migration is not backfilled.

## Sessions and API clients

Sessions expire after eight hours by default (absolute expiry, not idle timeout).
The session cookie is HttpOnly and SameSite=Strict; only its hash is stored in the
DB. A separate readable CSRF cookie supplies a token whose hash is also stored.
Passwords use salted scrypt hashes. Sessions/tokens are not kept in localStorage.

The browser frontend sends cookies, `Origin`, and the CSRF header automatically.
Scripts or Swagger requests must supply:

1. `POST /api/auth/login` with JSON username/password and an allowed `Origin`.
2. The returned cookies on later requests.
3. `X-CSRF-Token` matching the `dcim_csrf` cookie and an allowed `Origin` for
   POST/PATCH/DELETE requests, plus `X-Confirm-Action: yes` when required above.

Other account endpoints: `GET /api/auth/me`, `POST /api/auth/logout`,
`POST /api/auth/password`, and admin-only `GET/POST /api/users` and
`PATCH /api/users/{id}`. History: `GET /api/history`, optionally filtered by
`rack_id` or `system_id`, with `offset` and `limit` pagination.

## Deployment configuration

The supplied Compose configuration is for local development. Settings can be
provided through a root `.env` file (see [.env.example](../.env.example)):

| Setting | Local default | Purpose |
| --- | --- | --- |
| `SESSION_COOKIE_SECURE` | `false` | Set `true` for an HTTPS deployment so session/CSRF cookies are Secure |
| `SESSION_HOURS` | `8` | Absolute session lifetime; allowed range 1–168 hours |
| `CORS_ORIGINS` | localhost:5173 and 127.0.0.1:5173 origins | JSON array of exact permitted browser origins, including scheme and port |

After changing these settings, recreate the backend with
`docker compose up -d backend`; a plain restart does not replace its environment.
Do not enable Secure cookies while using ordinary local HTTP and expect sign-in
to work. A customer deployment still needs HTTPS, appropriate database credentials
and network exposure, global login rate limiting, backup/restore verification,
and a deployment/security review. API keys and per-customer tenancy are not implemented.

## Verification and next walkthrough

The last full implementation run on October 27 reported 41 passing tests, a
successful frontend production build, and a matching Alembic schema check. These
are historical results, not checks rerun by editing this document.

```bash
# Full suite, including database-backed integration/security tests
docker compose exec -e RUN_DB_TESTS=1 backend pytest -q

# Security-specific integration tests
docker compose exec -e RUN_DB_TESTS=1 backend pytest -q tests/test_security.py

# Driver and validation tests; database integration tests are skipped
docker compose exec backend pytest -q

# Frontend compilation and production bundle
docker compose exec frontend npm run build
```

Each database-backed test creates a unique temporary PostgreSQL schema, uses
independent request sessions, and removes that schema afterward. Existing inventory
is not used or changed. The test DB user needs schema creation/removal privileges;
an interrupted process may leave a `dcim_test_...` schema requiring manual inspection.

Browser inspection confirmed the first-admin/sign-in screen. It did not confirm
whether the user subsequently created their real administrator. The signed-in
walkthrough remains to be completed:

- Create viewer/operator accounts and verify their available controls.
- Check that canceling a power confirmation sends no command.
- Exercise permitted power actions and observe pending → completed history.
- Verify inventory/wiring/layout changes and a disposable rack deletion in history.
- Change a role/password, check session revocation, and sign out/in.
- Check the signed-in pages in both themes and at narrower widths.

Keep this scope separate from future real-hardware validation. Current telemetry
and command-completion observations are simulated.
