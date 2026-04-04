"""Input and configuration validators.

Validation is intentionally lightweight here — the heavy lifting
(field types, required checks) is delegated to Odoo's own schema
via OdooClient.get_model_schema(), called only when a client is
available. Config-level validation is fast and always runs first.
"""
from __future__ import annotations
from .errors import ValidationError


SUPPORTED_OPERATIONS = {"read", "create", "write", "delete"}


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


def validate_odoo_read_payload(payload: dict) -> None:
    """Validate the payload for an odoo_read action."""
    if "fields" in payload and not isinstance(payload["fields"], list):
        raise ValidationError("'fields' must be a list", {"fields": payload["fields"]})
    if "limit" in payload and not isinstance(payload["limit"], int):
        raise ValidationError("'limit' must be an integer", {"limit": payload["limit"]})
    if "domain" in payload and not isinstance(payload["domain"], list):
        raise ValidationError("'domain' must be a list", {"domain": payload["domain"]})


def validate_odoo_create_payload(payload: dict) -> None:
    """Validate the payload for an odoo_create action."""
    has_values = isinstance(payload.get("values"), dict) and payload["values"]
    has_template = bool(payload.get("template_id"))
    if not has_values and not has_template:
        raise ValidationError(
            "odoo_create requires either 'values' (dict) or 'template_id'",
            {"payload_keys": list(payload.keys())},
        )


def validate_odoo_write_payload(payload: dict) -> None:
    """Validate the payload for an odoo_write action."""
    if not isinstance(payload.get("ids"), list) or not payload["ids"]:
        raise ValidationError("odoo_write requires a non-empty 'ids' list")
    if not isinstance(payload.get("values"), dict) or not payload["values"]:
        raise ValidationError("odoo_write requires a non-empty 'values' dict")


def validate_odoo_delete_payload(payload: dict) -> None:
    """Validate the payload for an odoo_delete action."""
    if not isinstance(payload.get("ids"), list) or not payload["ids"]:
        raise ValidationError("odoo_delete requires a non-empty 'ids' list")


def validate_action_payload(action: str, payload: dict) -> None:
    """Dispatch-level payload validation — called before authorization."""
    if action == "odoo_read":
        validate_odoo_read_payload(payload)
    elif action == "odoo_create":
        validate_odoo_create_payload(payload)
    elif action == "odoo_write":
        validate_odoo_write_payload(payload)
    elif action == "odoo_delete":
        validate_odoo_delete_payload(payload)
    # meta actions (list_models, list_fields, rollback) need no payload validation
