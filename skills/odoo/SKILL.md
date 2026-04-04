---
name: odoo
description: Safe usage guidance for the Odoo plugin
---

# Odoo Skill

Use this connector as a bounded, deny-by-default Odoo integration.

All access is governed by **permission rules** configured by the user in the OpenClaw interface.
The agent cannot read, write, create, or delete anything unless the user has explicitly allowed it.

## Safety rules

- Never assume access is allowed — always respect what the rules permit.
- Never call arbitrary models or methods outside the registered tools.
- Never expose, request, or log secret values.
- Always prefer `odoo_read` before any write operation.
- Never delete unless explicitly told to and the user has enabled delete in the permission rules.
- If a `CONFIRMATION_REQUIRED` error is returned, ask the user to confirm before retrying with `confirmed: true`.

## Available tools

### Meta / discovery (always available)
- `odoo_list_models` — list all Odoo models on the active connection
- `odoo_list_fields` — list fields of a model with type metadata

### CRUD (access controlled by permission rules)
- `odoo_read` — read records from any model the user has allowed
- `odoo_create` — create a record (requires create rules per field)
- `odoo_write` — update records (requires write rules per field)
- `odoo_delete` — delete records (requires delete rule, always requires confirmation)

### Audit / recovery
- `odoo_rollback` — attempt to reverse a previous create or write

## Required behavior for writes

Before any create/write/delete:
1. Use `odoo_read` to confirm the current state.
2. Present the values you intend to write to the user.
3. Proceed only once intent is confirmed.
4. Honor `CONFIRMATION_REQUIRED` — do not bypass it.

## Rollback

- `create` → FULLY_REVERSIBLE (record can be deleted)
- `write` → FULLY_REVERSIBLE (previous values were snapshotted)
- `delete` → NOT_REVERSIBLE

Do not claim universal undo support. Be explicit about what is and is not recoverable.

## Error codes

| Code | Meaning |
|------|---------|
| `AUTHORIZATION_DENIED` | The permission rules do not allow this operation. Tell the user. |
| `CONFIRMATION_REQUIRED` | Policy requires `confirmed: true` before proceeding. |
| `VALIDATION_ERROR` | Invalid payload — check the required fields. |
| `SERVICE_ERROR` | Odoo connection issue. |
| `NOT_FOUND` | Profile or snapshot not found. |
