# OMOP - OpenClaw Odoo Connector

Safe-by-default OpenClaw plugin for Odoo, built around explicit profiles and deny-by-default permission rules.

This plugin does not expose arbitrary ORM or method execution. Every operation is evaluated on `(model, field, operation)` before the Odoo transport layer is called.

## Current scope

The plugin entrypoint exposes four bounded tools:

- `odoo_read`
- `odoo_create`
- `odoo_update`
- `odoo_delete`

Each tool accepts an explicit `profile` selection:

- `connection_profile_id`
- optional `access_profile_id`

Write operations are blocked globally when `read_only` is enabled.

## Structured configuration

The OpenClaw config schema supports these structured objects:

- `ConnectionProfile`
- `AccessProfile`
- `PermissionRule`
- `Template`

Key top-level fields:

- `active_connection_profile_id`
- `active_access_profile_id`
- `default_limit`
- `read_only`
- `connection_profiles[]`
- `access_profiles[]`
- `permission_rules[]`
- `templates[]`

Legacy fields are still accepted for compatibility:

- `baseUrl`
- `database`
- `profile`
- `readOnly`
- `defaultLimit`

## Security model

- deny by default when no rule matches
- authorization evaluated on `(model, field, operation)`
- confirmation enforced from access profile defaults plus rule overrides
- delete remains explicit and confirmation-aware
- secrets are resolved internally only
- the Odoo client handles transport only and never decides authorization

## Backend layout

Python modules are split by responsibility under [`python/odoo_connector`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector):

- profiles: [`connection_profiles.py`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector/connection_profiles.py), [`access_profiles.py`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector/access_profiles.py)
- rules: [`permission_rules.py`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector/permission_rules.py)
- validators: [`validators.py`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector/validators.py)
- executor: [`action_executor.py`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector/action_executor.py)
- logging: [`action_log.py`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector/action_log.py)
- snapshots: [`snapshot_store.py`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector/snapshot_store.py)
- rollback metadata: [`rollback_metadata.py`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector/rollback_metadata.py)
- rollback interface: [`rollback_service.py`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector/rollback_service.py)
- Odoo transport: [`odoo_client.py`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector/odoo_client.py)
- secrets: [`secret_service.py`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector/secret_service.py)
- errors: [`errors.py`](/c:/Users/supoe/OneDrive/Bureau/Projets/openclaw_odoo_plugin/python/odoo_connector/errors.py)

## Write pipeline

The current `create_task` flow is executed through `odoo_create` on model `project.task`, optionally via a `Template` with action `create_task`.

The pipeline enforces:

1. payload validation
2. deny-by-default authorization by `(model, field, operation)`
3. configurable confirmation requirement
4. snapshot creation before write execution
5. action logging
6. reversibility metadata attachment

Template-bound permission rules are supported through `template_ids`.

## Rollback status

Rollback metadata is available for create, write, and delete operations.

- `create`: `FULLY_REVERSIBLE` by intent
- `write`: `FULLY_REVERSIBLE` by intent
- `delete`: `NOT_REVERSIBLE`

Rollback execution itself is still stubbed in this iteration. The backend returns structured rollback metadata and status, but no compensating write is executed yet.

## Testing

Targeted unit tests cover:

- validator behavior
- permission evaluation
- `create_task` execution flow
- snapshot enrichment
- rollback metadata and stubbed interface
