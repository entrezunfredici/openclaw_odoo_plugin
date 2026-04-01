# AGENTS.md

## Mission

Build a safe, configurable OpenClaw plugin that provides an Odoo connector for AI agents.

This project is **generic at the UX level**, but **strictly constrained at the execution level**.

The connector must follow a **deny-by-default** model:
- no model access unless explicitly allowed
- no field access unless explicitly allowed
- no operation allowed unless explicitly allowed
- confirmation rules must be enforced when configured

This project must prioritize:
1. safety
2. access control
3. auditability
4. maintainability
5. predictable behavior

---

## Product intent

The goal is to build an OpenClaw plugin that lets a user:

- configure multiple Odoo connection profiles
- configure access profiles bound to those connections
- explicitly allow operations by model / field / operation
- choose whether confirmation is required for create / write / delete actions
- define reusable action templates
- keep a history of executed actions
- store enough previous state to support rollback when possible

This is **not** an unrestricted Odoo ORM proxy.

---

## Core concepts

Keep these concepts separated:

### 1. ConnectionProfile
Represents a connection to one Odoo instance.

Expected fields:
- id
- label
- base_url
- database
- login
- auth_type
- secret_ref
- api_mode
- enabled

### 2. AccessProfile
Represents the plugin-side authorization layer for a connection.

Expected fields:
- id
- label
- connection_profile_id
- enabled
- default_read_confirmation
- default_create_confirmation
- default_write_confirmation
- default_delete_confirmation

### 3. PermissionRule
Represents an explicit authorization rule.

Expected fields:
- model
- field or wildcard
- operation (`read`, `create`, `write`, `delete`)
- allowed
- require_confirmation
- optional template bindings

### 4. Template
Represents a reusable payload template for a bounded action.

### 5. ActionLog
Represents an executed action with metadata and result.

### 6. Snapshot
Represents the stored previous state used for rollback attempts.

Do not merge these concepts into one oversized config object.

---

## Architecture

Keep the repository split into 3 layers:

### A. OpenClaw plugin layer
Responsibilities:
- plugin manifest
- config loading
- tool registration
- optional admin routes / services
- bridge to Python backend

### B. Embedded skill layer
Responsibilities:
- teach the agent how to use the connector safely
- reinforce read-before-write behavior
- forbid unsafe exploration
- instruct the agent to stay within configured permissions

### C. Python backend
Responsibilities:
- Odoo communication
- profile management
- policy enforcement
- validation
- secret resolution
- action execution
- action logging
- snapshotting
- rollback support

Do not place all logic in the raw Odoo client.

---

## Tool design rules

Expose **bounded business actions** or **bounded admin actions** only.

Good examples:
- `odoo_list_tasks`
- `odoo_read_task`
- `odoo_create_task`
- `odoo_move_task`
- `odoo_add_comment`
- `odoo_list_connection_profiles`
- `odoo_create_connection_profile`
- `odoo_create_access_profile`
- `odoo_add_permission_rule`
- `odoo_preview_template`
- `odoo_rollback_action`

Bad examples:
- `odoo_execute_any_method`
- `odoo_write_any_model`
- `odoo_delete_anything`
- `odoo_list_all_models_without_policy`
- `odoo_manage_all_secrets`

Never expose arbitrary model/method execution to the agent.

---

## Security rules

Security is more important than convenience.

Always apply these rules:
- never use an Odoo admin account by default
- use dedicated technical accounts
- prefer API key based auth when supported
- enforce plugin-side policy even if Odoo ACLs already exist
- never allow access by default
- validate inputs before any Odoo call
- block delete by default unless explicitly enabled
- never expose secrets as a generic tool
- never log secrets
- never print secrets in tool output
- require confirmation when the configured policy says so

If a request is ambiguous, stop and ask for clarification instead of guessing.

---

## Authorization model

Authorization must be evaluated on:

- connection profile
- access profile
- operation
- model
- field(s)

The minimal decision unit is:

`(model, field, operation)`

Not just:
`(model, field)`

Every execution should produce a decision result internally, for example:
- allowed / denied
- confirmation required / not required
- matching rule id
- reason

---

## Odoo client rules

Treat the Odoo client as a low-level transport layer only.

It may:
- connect
- search / read
- create
- write
- delete

It must not decide:
- whether an action is allowed
- whether a field is allowed
- whether confirmation is required
- whether rollback is possible

That logic belongs to:
- policy layer
- validators
- action executor
- rollback service

---

## Rollback rules

Rollback is a product feature, but it must be implemented carefully.

Do not claim that all actions are fully reversible.

Each action should declare one of:
- `FULLY_REVERSIBLE`
- `PARTIALLY_REVERSIBLE`
- `NOT_REVERSIBLE`

Before any write or delete action, store the previous relevant state in a snapshot.

Rollback should use:
- the action log
- the stored snapshot
- the reversibility level of the action

If rollback cannot be guaranteed, say so explicitly.

---

## Templates rules

Templates must stay bounded to known actions.

Allowed:
- task creation template
- task move template
- chatter note template

Not allowed:
- generic template for arbitrary model/method execution

Every template must:
- declare required variables
- validate payload shape before execution
- support preview before write when possible

---

## Secrets rules

Secrets are infrastructure concerns, not agent tools.

Allowed:
- internal secret resolution by profile
- lookup of login / password / API key from a secret reference

Forbidden:
- generic secret browsing
- secret editing by the agent unless explicitly implemented as an admin-only bounded flow
- printing secret values

---

## Repository structure

Prefer a structure close to this:

- `openclaw.plugin.json`
- `README.md`
- `AGENTS.md`
- `src/`
- `skills/odoo/SKILL.md`
- `python/odoo_connector/`
- `tests/`

Suggested Python modules:
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

---

## Implementation strategy

Implement in phases.

### Phase 1
Scaffold the plugin and backend:
- plugin manifest
- plugin entrypoint
- Python bridge
- minimal README
- embedded skill
- data models / persistence stubs

### Phase 2
Implement admin foundations:
- connection profiles
- access profiles
- permission rules
- template storage
- action log storage
- snapshot storage

### Phase 3
Implement safe Odoo execution:
- read flows
- create / write flows
- confirmation handling
- action logging
- snapshotting

### Phase 4
Implement rollback support:
- reversibility metadata
- rollback execution
- rollback limitations reporting

Do not jump directly to full feature breadth.

---

## Coding rules

When editing this repository:
- prefer small, clear files
- avoid speculative abstractions
- keep naming explicit
- keep code testable
- use type hints in Python where useful
- return structured errors
- keep logs useful but never sensitive
- document config fields and new tools

If commands are missing in the repo, do not invent a fake workflow silently.
Add only what is justified by the current implementation.

---

## Testing expectations

Priority tests:
- validators
- permission evaluation
- profile loading
- action execution
- snapshot creation
- rollback decision logic

Do not consider write flows complete without tests.

---

## Documentation expectations

When changing behavior or architecture:
- update `README.md`
- keep examples aligned with real code
- document new config fields
- document new tools
- document rollback limitations
- document security implications

---

## Review checklist

Before considering work complete, verify:

- Is the action bounded?
- Is authorization checked?
- Is confirmation logic checked?
- Is validation present?
- Are secrets protected?
- Is the action logged?
- Is previous state snapshotted when relevant?
- Is rollback capability declared honestly?
- Is the code documented?
- Are tests updated?

If any answer is "no", the work is incomplete.

---

## What not to do

Do not:
- expose full unrestricted Odoo access
- expose arbitrary model / method execution
- rely only on Odoo ACLs for safety
- claim universal rollback support
- merge transport, policy, validation, logging, and rollback into one giant file
- expose secrets as a normal agent capability

---

## Working style for Codex

When working on large changes:
1. first inspect the repository
2. summarize the current structure
3. propose a short implementation plan
4. then implement incrementally
5. update docs if behavior changes

If the task is large, create or update a plan file before major edits.

When recurring mistakes are corrected by the user, update this `AGENTS.md` so future sessions inherit the fix.