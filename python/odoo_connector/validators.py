"""Input and configuration validators."""

from __future__ import annotations

from typing import Any

from .errors import ValidationError


CRUD_ACTIONS = {"odoo_read", "odoo_create", "odoo_update", "odoo_write", "odoo_delete"}


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
        raise ValidationError(
            "Connector config is missing required fields",
            {"missing": missing},
        )


def validate_model_name(action: str, model: str) -> None:
    if action in CRUD_ACTIONS and (not isinstance(model, str) or not model.strip()):
        raise ValidationError(
            f"{action} requires a non-empty model name",
            {"action": action, "model": model},
        )


def validate_odoo_read_payload(payload: dict) -> None:
    if "fields" in payload:
        if not isinstance(payload["fields"], list) or not all(isinstance(item, str) for item in payload["fields"]):
            raise ValidationError("'fields' must be a list of strings", {"fields": payload["fields"]})
    if "limit" in payload and not isinstance(payload["limit"], int):
        raise ValidationError("'limit' must be an integer", {"limit": payload["limit"]})
    filters = payload.get("filters", payload.get("domain"))
    if filters is not None and not isinstance(filters, list):
        raise ValidationError("'filters' must be a list", {"filters": filters})


def validate_odoo_create_payload(payload: dict) -> None:
    has_values = isinstance(payload.get("values"), dict) and bool(payload["values"])
    has_template = isinstance(payload.get("template_id"), str) and bool(payload["template_id"].strip())
    if not has_values and not has_template:
        raise ValidationError(
            "odoo_create requires either 'values' (dict) or 'template_id'",
            {"payload_keys": list(payload.keys())},
        )


def _is_int_like(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_create_task_values(values: dict[str, Any]) -> None:
    missing = [field for field in ("name", "project_id") if field not in values]
    if missing:
        raise ValidationError(
            "create_task requires 'name' and 'project_id'",
            {"missing": missing},
        )
    if not isinstance(values["name"], str) or not values["name"].strip():
        raise ValidationError("create_task requires a non-empty string for 'name'")
    if not _is_int_like(values["project_id"]):
        raise ValidationError("create_task requires an integer 'project_id'")
    if "description" in values and not isinstance(values["description"], str):
        raise ValidationError("create_task expects 'description' to be a string", {"description": values["description"]})


def validate_create_values_for_model(model: str, values: dict[str, Any], template_action: str | None = None) -> None:
    if not isinstance(values, dict) or not values:
        raise ValidationError("Create requires a non-empty values payload", {"model": model})

    if template_action == "create_task" or model == "project.task":
        validate_create_task_values(values)


def validate_odoo_update_payload(payload: dict) -> None:
    if not _is_int_like(payload.get("id")):
        raise ValidationError("odoo_update requires an integer 'id'", {"id": payload.get("id")})
    if not isinstance(payload.get("values"), dict) or not payload["values"]:
        raise ValidationError("odoo_update requires a non-empty 'values' dict")


def validate_odoo_write_payload(payload: dict) -> None:
    if _is_int_like(payload.get("id")):
        validate_odoo_update_payload(payload)
        return
    if not isinstance(payload.get("ids"), list) or not payload["ids"]:
        raise ValidationError("odoo_write requires a non-empty 'ids' list")
    if not all(_is_int_like(item) for item in payload["ids"]):
        raise ValidationError("odoo_write requires integer ids only", {"ids": payload["ids"]})
    if not isinstance(payload.get("values"), dict) or not payload["values"]:
        raise ValidationError("odoo_write requires a non-empty 'values' dict")


def validate_odoo_delete_payload(payload: dict) -> None:
    if _is_int_like(payload.get("id")):
        return
    if not isinstance(payload.get("ids"), list) or not payload["ids"]:
        raise ValidationError("odoo_delete requires either an integer 'id' or a non-empty 'ids' list")
    if not all(_is_int_like(item) for item in payload["ids"]):
        raise ValidationError("odoo_delete requires integer ids only", {"ids": payload["ids"]})


def validate_action_payload(action: str, payload: dict, model: str = "") -> None:
    validate_model_name(action, model)

    if action == "odoo_read":
        validate_odoo_read_payload(payload)
    elif action == "odoo_create":
        validate_odoo_create_payload(payload)
    elif action == "odoo_update":
        validate_odoo_update_payload(payload)
    elif action == "odoo_write":
        validate_odoo_write_payload(payload)
    elif action == "odoo_delete":
        validate_odoo_delete_payload(payload)
