"""CLI bridge for TypeScript plugin -> Python backend execution."""

from __future__ import annotations

import json, sys

from .action_executor import ActionExecutor
from .errors import ConnectorError


def main() -> None:
    raw = sys.stdin.read()
    data = json.loads(raw)

    client = data.get("client")
    model = data.get("model")
    action = data.get("action")
    payload = data.get("payload", {})
    config = payload.pop("config", {})

    executor = ActionExecutor()
    try:
        result = executor.execute(client, model, action, payload, config)
    except ConnectorError as exc:
        print(json.dumps(exc.to_dict()))
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "code": "UNHANDLED_ERROR",
                        "message": str(exc),
                        "details": {},
                    },
                }
            )
        )
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
