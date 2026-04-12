import unittest

from python.odoo_connector.permission_rules import PermissionRule, PermissionRuleEngine


class PermissionRuleEngineTest(unittest.TestCase):
    def test_deny_by_default_when_no_rule_matches(self) -> None:
        engine = PermissionRuleEngine([])

        decision = engine.evaluate(
            access_profile_id="ops",
            model="project.task",
            operation="read",
            fields=["name"],
            default_confirmation=False,
        )

        self.assertFalse(decision.allowed)

    def test_explicit_deny_beats_allow(self) -> None:
        engine = PermissionRuleEngine(
            [
                PermissionRule("allow_all", "ops", "project.task", "*", "read", True),
                PermissionRule("deny_name", "ops", "project.task", "name", "read", False),
            ]
        )

        decision = engine.evaluate(
            access_profile_id="ops",
            model="project.task",
            operation="read",
            fields=["name"],
            default_confirmation=False,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.matched_rule_ids, ["deny_name"])

    def test_template_binding_requires_matching_template(self) -> None:
        engine = PermissionRuleEngine(
            [
                PermissionRule(
                    "task_tpl_name",
                    "ops",
                    "project.task",
                    "name",
                    "create",
                    True,
                    template_ids=["task_template"],
                )
            ]
        )

        allowed_without_template = engine.is_field_allowed(
            access_profile_id="ops",
            model="project.task",
            operation="create",
            field="name",
        )
        allowed_with_template = engine.is_field_allowed(
            access_profile_id="ops",
            model="project.task",
            operation="create",
            field="name",
            template_id="task_template",
        )

        self.assertFalse(allowed_without_template)
        self.assertTrue(allowed_with_template)

    def test_confirmation_flag_is_aggregated_from_rules(self) -> None:
        engine = PermissionRuleEngine(
            [
                PermissionRule("task_name", "ops", "project.task", "name", "create", True, True),
                PermissionRule("task_project", "ops", "project.task", "project_id", "create", True, False),
            ]
        )

        decision = engine.evaluate(
            access_profile_id="ops",
            model="project.task",
            operation="create",
            fields=["name", "project_id"],
            default_confirmation=False,
        )

        self.assertTrue(decision.allowed)
        self.assertTrue(decision.require_confirmation)


if __name__ == "__main__":
    unittest.main()
