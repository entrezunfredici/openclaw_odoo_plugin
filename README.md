# OMOP - OpenClaw Odoo Connector (Safe by Default)

A deny-by-default OpenClaw plugin that provides bounded Odoo actions for AI agents.

> This project is intentionally **not** a generic Odoo ORM proxy.

## Current implementation status (this iteration)

Implemented now:
- plugin entrypoint with two bounded tools:
  - `odoo_list_tasks` (safe read)
  - `odoo_create_task` (bounded write)
- structured config support for:
  - `ConnectionProfile`
  - `AccessProfile`
  - `PermissionRule`
  - `Template`
- Python backend modules split by responsibility:
  - profiles, rules, validators, executor, logging, snapshots, rollback metadata, Odoo transport, secrets, errors
- write pipeline for `create_task` enforces:
  - payload validation
  - deny-by-default authorization by `(model, field, operation)`
  - configurable confirmation requirement
  - snapshot creation before write execution
  - action logging
- rollback interface + reversibility metadata (rollback execution is still stubbed)

Not implemented yet:
- persistent storage (current logs/snapshots are in-memory)
- bounded admin tools for profile/rule/template management
- additional bounded business actions beyond `list_tasks` and `create_task`
- rollback execution implementation

## Safety model

- no access unless explicitly allowed by permission rule
- authorization decision unit is `(model, field, operation)`
- read and write confirmations come from access profile defaults, then rule overrides
- global `read_only` blocks write actions
- raw Odoo client does transport only (no policy decisions)
- secrets are resolved internally and never returned in tool output

## Repository layout

- `src/` → OpenClaw plugin layer (tool registration + config + Python bridge)
- `skills/odoo/SKILL.md` → embedded safe usage instructions
- `python/odoo_connector/` → backend services

Key backend modules:
- `connection_profiles.py`
- `access_profiles.py`
- `permission_rules.py`
- `templates.py`
- `action_executor.py`
- `action_log.py`
- `snapshot_store.py`
- `rollback_service.py`
- `odoo_client.py`
- `validators.py`
- `secret_service.py`
- `errors.py`

## Configuration

The plugin now accepts structured config fields in `openclaw.plugin.json`:
- `active_connection_profile_id`
- `active_access_profile_id`
- `default_limit`
- `read_only`
- `connection_profiles[]`
- `access_profiles[]`
- `permission_rules[]`
- `templates[]`

Legacy compatibility fields (`baseUrl`, `database`, `profile`, `readOnly`, `defaultLimit`) are still mapped into a default connection/access setup for incremental migration.

## Action behavior

### `odoo_list_tasks`
- Operation: read
- Model: `project.task`
- Required input: `project_id`
- Optional input: `limit`

### `odoo_create_task`
- Operation: create
- Model: `project.task`
- Required input: `project_id`, `name`
- Optional input: `description`, `confirmed`
- Enforcement chain:
  1. validation
  2. authorization rules by field
  3. confirmation policy check
  4. action log start
  5. snapshot creation
  6. Odoo create call
  7. action log success

## Security notes

- Delete is not exposed in this iteration.
- Arbitrary model/method execution is not exposed.
- Template handling is bounded to known actions (`create_task` currently).
- Secrets are resolved from `ODOO_SECRET_<SECRET_REF>` or keyring fallback.

## TODO - next iteration

1. Add persistent stores for action logs, snapshots, profiles, rules, and templates.
2. Add bounded admin actions for managing profiles/rules/templates.
3. Add one safe bounded write update flow (for example move task stage) with snapshot + rollback metadata.
4. Implement rollback execution for supported reversible actions.
5. Add tests for validators, permission evaluation, executor flow, snapshot creation, and rollback decisions.
