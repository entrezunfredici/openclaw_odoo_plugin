def validate_action_payload(action: str, payload: dict) -> None:
    if action == "list_tasks":
        if "project_id" not in payload:
            raise Exception("Missing 'project_id'")
        return

    if action == "create_task":
        if "project_id" not in payload:
            raise Exception("Missing 'project_id'")
        if "name" not in payload or not payload["name"]:
            raise Exception("Missing or empty 'name'")
        return

    raise Exception(f"Unsupported action '{action}'")
