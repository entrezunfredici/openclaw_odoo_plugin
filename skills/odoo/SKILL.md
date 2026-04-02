---
name: odoo
description: Safe usage guidance for the Odoo plugin
---

# Odoo Skill

Use this connector as a bounded, deny-by-default Odoo integration.

## Safety rules

- Never assume access is allowed.
- Never call arbitrary models or arbitrary methods.
- Never expose or request secret values.
- Always prefer read-before-write when possible.
- Do not use delete unless an explicit bounded delete tool exists and policy allows it.

## Current bounded actions

- `odoo_list_tasks` (read)
- `odoo_create_task` (create)

No generic CRUD execution is available.

## Required behavior for writes

Before writing:
1. confirm intent and required values,
2. verify scope and permissions,
3. honor confirmation policy.

If `confirmed` is required by policy and not provided, ask for confirmation before retrying.

## Rollback expectation

Rollback is not guaranteed.

For write actions, treat rollback as best-effort and explicitly communicate limitations.
Do not claim universal undo support.
