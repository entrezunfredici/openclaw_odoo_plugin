import unittest

from python.odoo_connector.errors import ValidationError
from python.odoo_connector.validators import validate_action_payload, validate_create_values_for_model


class ValidatorsTest(unittest.TestCase):
    def test_update_payload_accepts_single_id(self) -> None:
        validate_action_payload(
            "odoo_update",
            {"id": 5, "values": {"name": "Renamed"}},
            "project.task",
        )

    def test_update_payload_rejects_missing_single_id(self) -> None:
        with self.assertRaises(ValidationError):
            validate_action_payload(
                "odoo_update",
                {"ids": [5], "values": {"name": "Renamed"}},
                "project.task",
            )

    def test_read_payload_rejects_non_list_filters(self) -> None:
        with self.assertRaises(ValidationError):
            validate_action_payload(
                "odoo_read",
                {"filters": "not-a-domain"},
                "project.task",
            )

    def test_create_task_requires_name_and_project_id(self) -> None:
        with self.assertRaises(ValidationError):
            validate_create_values_for_model("project.task", {"name": "Task only"})


if __name__ == "__main__":
    unittest.main()
