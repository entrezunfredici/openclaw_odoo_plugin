"""CLI bridge for TypeScript plugin -> Python backend execution.

Input (stdin JSON):
  {
    "action": "odoo_read" | "odoo_create" | "odoo_update" | "odoo_write" | "odoo_delete"
            | "odoo_list_models" | "odoo_list_fields" | "odoo_rollback",
    "model":   "project.task",   // omitted for meta actions
    "payload": { ...params... },
    "config":  { ...pluginConfig... }
  }

Output (stdout JSON):
  { "ok": true, ... }
  { "ok": false, "error": { "code": "...", "message": "...", "details": {} } }
"""

from __future__ import annotations

import json
import sys

from .action_executor import ActionExecutor
from .errors import ConnectorError


def main() -> None:
    raw = sys.stdin.read()
    data = json.loads(raw)

    action: str = data.get("action", "")
    model: str = data.get("model", "")
    payload: dict = data.get("payload", {})
    config: dict = data.get("config", {})

    executor = ActionExecutor()
    try:
        result = executor.execute(action, model, payload, config)
    except ConnectorError as exc:
        print(json.dumps(exc.to_dict()))
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({
            "ok": False,
            "error": {
                "code": "UNHANDLED_ERROR",
                "message": str(exc),
                "details": {},
            },
        }))
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
