
# Odoo OpenClaw Plugin

![Status](https://img.shields.io/badge/status-WIP-orange)
![OpenClaw](https://img.shields.io/badge/OpenClaw-plugin-blue)
![Odoo](https://img.shields.io/badge/Odoo-safe%20connector-875A7B)
![License](https://img.shields.io/badge/license-TBD-lightgrey)

A safe and configurable OpenClaw plugin for connecting an AI agent to Odoo.

This project is built around one principle:

> **Do not give an agent unrestricted ERP access.**
> Expose only bounded, validated, auditable business actions.

---

## Why this plugin exists

Most "generic Odoo connectors" are too broad for agent usage.

They usually allow:

- unrestricted model browsing
- arbitrary create/update/delete operations
- fuzzy object creation
- excessive permissions
- weak auditability

This plugin takes the opposite approach:

- narrow business scope
- explicit tool definitions
- access control by profile
- validation before every Odoo call
- write protection by default
- audit logging for sensitive actions

---

## Features

Current / planned capabilities:

- List projects
- List project tasks
- Read task details
- Create a task
- Move a task to another stage
- Add a comment / chatter message
- Enforce access policies by profile
- Keep Odoo credentials internal to the connector
- Log write operations for later review

---

## Architecture

This project is split into three layers:

### 1. OpenClaw plugin layer

Responsible for:

- plugin registration
- tool registration
- configuration loading
- config validation
- bridge to the Python backend
- OpenClaw-facing responses

### 2. Embedded skill layer

Responsible for:

- teaching the agent when to use the tools
- describing the allowed workflow
- reinforcing safety boundaries
- discouraging unsafe or ambiguous actions

### 3. Python Odoo core

Responsible for:

- Odoo communication
- payload validation
- access policy enforcement
- secret resolution
- business action execution
- clean domain/service errors

---

## Project structure

```text
odoo-openclaw-plugin/
├── package.json
├── openclaw.plugin.json
├── tsconfig.json
├── README.md
├── src/
│   ├── index.ts
│   ├── tools/
│   │   ├── registerTools.ts
│   │   ├── listTasks.ts
│   │   ├── readTask.ts
│   │   ├── createTask.ts
│   │   ├── moveTask.ts
│   │   └── addComment.ts
│   ├── config/
│   │   ├── resolveConfig.ts
│   │   └── defaults.ts
│   ├── runtime/
│   │   ├── pythonBridge.ts
│   │   └── auditLogger.ts
│   └── types/
│       └── plugin.ts
├── skills/
│   └── odoo/
│       └── SKILL.md
├── python/
│   └── odoo_connector/
│       ├── __init__.py
│       ├── cli.py
│       ├── odoo_client.py
│       ├── access_policy.py
│       ├── validators.py
│       ├── secret_service.py
│       ├── errors.py
│       └── actions/
│           ├── list_tasks.py
│           ├── read_task.py
│           ├── create_task.py
│           ├── move_task.py
│           └── add_comment.py
└── tests/
    ├── plugin/
    └── python/
```
