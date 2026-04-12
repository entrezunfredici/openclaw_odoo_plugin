import unittest
from unittest.mock import patch

from python.odoo_connector.action_executor import ActionExecutor
from python.odoo_connector.errors import AuthorizationError, ConfirmationRequiredError


def build_config(template_bound: bool = False) -> dict:
    rules = [
        {
            "id": "task_name_create",
            "access_profile_id": "project_ops",
            "model": "project.task",
            "field": "name",
            "operation": "create",
            "allowed": True,
            "require_confirmation": True,
        },
        {
            "id": "task_project_create",
            "access_profile_id": "project_ops",
            "model": "project.task",
            "field": "project_id",
            "operation": "create",
            "allowed": True,
            "require_confirmation": True,
        },
    ]
    if template_bound:
        for rule in rules:
            rule["template_ids"] = ["task_template"]

    return {
        "active_connection_profile_id": "default",
        "active_access_profile_id": "project_ops",
        "default_limit": 25,
        "read_only": False,
        "connection_profiles": [
            {
                "id": "default",
                "label": "Default",
                "base_url": "https://odoo.example.com",
                "database": "odoo",
                "login": "bot@example.com",
                "auth_type": "api_key",
                "secret_ref": "default",
                "api_mode": "jsonrpc",
                "enabled": True,
                "port": 443,
            }
        ],
        "access_profiles": [
            {
                "id": "project_ops",
                "label": "Project Ops",
                "connection_profile_id": "default",
                "enabled": True,
                "default_read_confirmation": False,
                "default_create_confirmation": False,
                "default_write_confirmation": True,
                "default_delete_confirmation": True,
            }
        ],
        "permission_rules": rules,
        "templates": [
            {
                "id": "task_template",
                "label": "Task template",
                "action": "create_task",
                "required_variables": ["name", "project_id"],
                "payload_template": {
                    "name": "{name}",
                    "project_id": "{project_id}",
                },
                "enabled": True,
            }
        ],
    }


class FakeOdooClient:
    def __init__(self) -> None:
        self.post_calls: list[tuple[str, dict]] = []

    def post(self, model_name: str, values: dict) -> int:
        self.post_calls.append((model_name, values))
        return 42

    def get(self, model_name, domain, fields, limit):  # noqa: ANN001
        return [{"id": 42, "name": "Task"}]

    def put(self, model_name, object_ids, values):  # noqa: ANN001
        return True

    def delete(self, model_name, object_ids):  # noqa: ANN001
        return True


class ActionExecutorCreateTaskTest(unittest.TestCase):
    def test_create_task_requires_confirmation(self) -> None:
        executor = ActionExecutor()
        fake_client = FakeOdooClient()

        with patch("python.odoo_connector.action_executor.SecretService.get_secret", return_value="secret"), patch(
            "python.odoo_connector.action_executor.OdooClient",
            return_value=fake_client,
        ):
            with self.assertRaises(ConfirmationRequiredError):
                executor.execute(
                    "odoo_create",
                    "project.task",
                    {"values": {"name": "Task", "project_id": 7}},
                    build_config(),
                )

    def test_create_task_creates_snapshot_and_action_log(self) -> None:
        executor = ActionExecutor()
        fake_client = FakeOdooClient()

        with patch("python.odoo_connector.action_executor.SecretService.get_secret", return_value="secret"), patch(
            "python.odoo_connector.action_executor.OdooClient",
            return_value=fake_client,
        ):
            result = executor.execute(
                "odoo_create",
                "project.task",
                {
                    "template_id": "task_template",
                    "variables": {"name": "Task", "project_id": 7},
                    "confirmed": True,
                },
                build_config(template_bound=True),
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["record_id"], 42)
        self.assertEqual(fake_client.post_calls, [("project.task", {"name": "Task", "project_id": 7})])

        snapshots = executor.snapshot_store.list_snapshots()
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].record_ids, [42])

        action_logs = executor.action_log.list_entries()
        self.assertEqual(len(action_logs), 1)
        self.assertEqual(action_logs[0].status, "succeeded")
        self.assertEqual(action_logs[0].metadata["reversibility"]["level"], "FULLY_REVERSIBLE")

    def test_create_task_is_denied_without_matching_template_binding(self) -> None:
        executor = ActionExecutor()
        fake_client = FakeOdooClient()

        with patch("python.odoo_connector.action_executor.SecretService.get_secret", return_value="secret"), patch(
            "python.odoo_connector.action_executor.OdooClient",
            return_value=fake_client,
        ):
            with self.assertRaises(AuthorizationError):
                executor.execute(
                    "odoo_create",
                    "project.task",
                    {
                        "values": {"name": "Task", "project_id": 7},
                        "confirmed": True,
                    },
                    build_config(template_bound=True),
                )


if __name__ == "__main__":
    unittest.main()
