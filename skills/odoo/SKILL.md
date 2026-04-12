---
name: odoo
description: Safe usage guidance for the Odoo plugin
---

# Odoo Skill

Use this connector as a bounded, deny-by-default Odoo integration.

All access is governed by permission rules configured by the user in the OpenClaw interface. The agent cannot read, create, update, or delete anything unless the configured rules explicitly allow it.

## Safety rules

- Never assume access is allowed.
- Never expose or request secret values.
- Prefer `odoo_read` before any write.
- Never bypass `CONFIRMATION_REQUIRED`.
- Treat delete as high risk and non-reversible.

## Available tools

- `odoo_read`
- `odoo_create`
- `odoo_update`
- `odoo_delete`

Each tool must be called with a `profile` object:

- `connection_profile_id`
- optional `access_profile_id`

## Required behavior for writes

Before any create, update, or delete:

1. use `odoo_read` when you need to confirm current state
2. present the intended change clearly to the user
3. proceed only after intent is explicit
4. if the backend returns `CONFIRMATION_REQUIRED`, ask the user to confirm before retrying with `confirmed: true`

## Templates

- Templates are bounded to known actions only.
- `create_task` templates must be used with model `project.task`.
- Permission rules may restrict which template ids are allowed.

## Rollback

- Reversibility metadata exists internally.
- Rollback execution is still stubbed in this iteration.
- Do not claim that undo is operational yet.

## Error codes

| Code | Meaning |
|------|---------|
| `AUTHORIZATION_DENIED` | The permission rules do not allow this operation. |
| `CONFIRMATION_REQUIRED` | Policy requires `confirmed: true` before proceeding. |
| `VALIDATION_ERROR` | Invalid payload or unsupported model/template combination. |
| `SERVICE_ERROR` | Odoo connection or transport failure. |
| `NOT_FOUND` | Profile, template, or snapshot not found. |
