"""Input and configuration validators."""

from __future__ import annotations

from .errors import ValidationError

SUPPORTED_ACTIONS = {"list_tasks", "create_task"}


def validate_config(config: dict) -> None:
    required = [
        "active_connection_profile_id",
        "active_access_profile_id",
        "connection_profiles",
        "access_profiles",
        "permission_rules",
    ]
    missing = [key for key in required if key not in config]
    if missing:
        raise ValidationError("Connector config is missing required fields", {"missing": missing})


def validate_action_payload(action: str, payload: dict) -> None:
    if action not in SUPPORTED_ACTIONS:
        raise ValidationError("Unsupported action", {"action": action})

    if action == "list_tasks":
        if "project_id" not in payload:
            raise ValidationError("Missing required field 'project_id'")
        if not isinstance(payload["project_id"], int):
            raise ValidationError("'project_id' must be an integer")
        if "limit" in payload and not isinstance(payload["limit"], int):
            raise ValidationError("'limit' must be an integer when provided")
        return

    if action == "create_task":
        if "project_id" not in payload:
            raise ValidationError("Missing required field 'project_id'")
        if "name" not in payload:
            raise ValidationError("Missing required field 'name'")
        if not isinstance(payload["project_id"], int):
            raise ValidationError("'project_id' must be an integer")
        if not isinstance(payload["name"], str) or not payload["name"].strip():
            raise ValidationError("'name' must be a non-empty string")
        if "description" in payload and not isinstance(payload["description"], str):
            raise ValidationError("'description' must be a string when provided")
        if "confirmed" in payload and not isinstance(payload["confirmed"], bool):
            raise ValidationError("'confirmed' must be a boolean when provided")
        return
