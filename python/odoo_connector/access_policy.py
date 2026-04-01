class OdooAccessPolicy:
    ALLOWED_ACTIONS = {
        "readonly": {"list_tasks"},
        "project_ops": {"list_tasks", "create_task"},
    }

    @classmethod
    def check_action(cls, action: str, profile: str) -> None:
        allowed = cls.ALLOWED_ACTIONS.get(profile, set())
        if action not in allowed:
            raise Exception(f"Action '{action}' is forbidden for profile '{profile}'")
