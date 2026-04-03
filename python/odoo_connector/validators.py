"""Input and configuration validators."""
from __future__ import annotations
from .errors import ValidationError
from .odoo_client import OdooClient

SUPPORTED_ACTIONS = {
    "project.task":["c", "r"]
}

SPECIFIC_RULES = {
    "prokject.task":[
        {
            "action":"c",
            "subject": "description",
            "operation": "in",
            "compared":"payload",
            "message":"'description' must be in payload"
        },
        {
            "action":"c",
            "subject": "confirmed",
            "operation": "in",
            "compared":"payload",
            "message":"'description' must be a string when provided"
        }
    ]
}


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
    return True

def validate_fields(client: OdooClient, model: str, payload: dict):
    verif = client.get_model_schema(model)
    for field in payload.keys():
        if verif[field]["required"] and not payload[field].strip() :
            raise ValidationError(f"Missing required field {field} in model {model}")
        if not isinstance(payload[field], verif[field]["ttype"]):
            raise ValidationError(f"{field} must be an {verif[field]["ttype"]}")
    return

def validate_rules(model: str, action: str, payload: dict):
    for rule in SPECIFIC_RULES[model]:
        if rule["action"] == action :
            match(rule["operation"]):
                case "==":
                    if not (payload[rule["subject"]] == payload[rule["compared"]]):
                        raise ValidationError(rule["description"])
                case "!=":
                    if not (payload[rule["subject"]] != payload[rule["compared"]]):
                        raise ValidationError(rule["description"])
                case ">=":
                    if not (payload[rule["subject"]] >= payload[rule["compared"]]):
                        raise ValidationError(rule["description"])
                case "<=":
                    if not (payload[rule["subject"]] <= payload[rule["compared"]]):
                        raise ValidationError(rule["description"])
                case ">":
                    if not (payload[rule["subject"]] > payload[rule["compared"]]):
                        raise ValidationError(rule["description"])
                case "<":
                    if not (payload[rule["subject"]] < payload[rule["compared"]]):
                        raise ValidationError(rule["description"])
                case "in":
                    if not (payload[rule["subject"]] in payload[rule["compared"]]):
                        raise ValidationError(rule["description"])
                case "not in":
                    if not (payload[rule["subject"]] not in payload[rule["compared"]]):
                        raise ValidationError(rule["description"])
    return


def validate_action_payload(client: OdooClient, model: str, action: str, payload: dict) -> None:
    if action not in SUPPORTED_ACTIONS[model]:
        raise ValidationError("Unsupported action", {"action": action})

    validate_rules(model, action, payload)
    validate_fields(client, model, payload)

    if action == "c":
        return

    if action == "r":
        if "limit" in payload and not isinstance(payload["limit"], int):
            raise ValidationError("'limit' must be an integer when provided")
        return

    if action == "u":
        return

    if action == "d":
        return
