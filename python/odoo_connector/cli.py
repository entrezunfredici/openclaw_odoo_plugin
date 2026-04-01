import json
import sys

from python.odoo_connector.odoo_client import OdooClient
from python.odoo_connector.access_policy import OdooAccessPolicy
from python.odoo_connector.validators import validate_action_payload
from secret_service import SecretService


def main():
    raw = sys.stdin.read()
    data = json.loads(raw)

    action = data["action"]
    payload = data["payload"]

    validate_action_payload(action, payload)

    secret_service = SecretService("odoo-plugin")
    login = secret_service.get_secret("login")
    password = secret_service.get_secret("password")

    client = OdooClient(
        url="odoo.example.com",
        port=443,
        database="my_database",
        login=login,
        password=password,
    )

    if action == "list_tasks":
        OdooAccessPolicy.check_action("list_tasks", payload.get("profile", "readonly"))
        result = client.get(
            "project.task",
            [["project_id", "=", payload["project_id"]]],
            ["id", "name", "stage_id", "project_id"],
            payload.get("limit", 25),
        )
        print(json.dumps(result))
        return

    if action == "create_task":
        OdooAccessPolicy.check_action("create_task", payload.get("profile", "readonly"))
        if payload.get("readOnly", True):
            raise Exception("Plugin is in read-only mode")

        task_id = client.post("project.task", {
            "project_id": payload["project_id"],
            "name": payload["name"],
            "description": payload.get("description", "")
        })
        print(json.dumps({"task_id": task_id}))
        return

    raise Exception(f"Unknown action: {action}")


if __name__ == "__main__":
    main()
