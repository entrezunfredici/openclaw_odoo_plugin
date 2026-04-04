"""Generic action executor — model-agnostic, fully driven by config.

All access decisions pass through the PermissionRuleEngine before any
Odoo call is made. The executor never hard-codes model names or fields.
"""

from __future__ import annotations

from typing import Any

from .access_profiles import AccessProfiles
from .action_log import ActionLogStore
from .connection_profiles import ConnectionProfiles
from .errors import AuthorizationError, ConfirmationRequiredError, ValidationError
from .model_metadata_service import ModelMetadataService
from .odoo_client import OdooClient
from .permission_rules import PermissionRuleEngine
from .rollback_service import RollbackService
from .secret_service import SecretService
from .snapshot_store import SnapshotStore
from .templates import TemplateStore
from .validators import validate_config


class ActionExecutor:
    """Coordinates validation, authorization, snapshotting, logging, and execution."""

    def __init__(self) -> None:
        self.action_log = ActionLogStore()
        self.snapshot_store = SnapshotStore()
        self.rollback_service = RollbackService(self.snapshot_store)
        self.metadata_service = ModelMetadataService()

    def execute(
        self,
        action: str,
        model: str,
        payload: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        validate_config(config)

        connection_profiles = ConnectionProfiles.from_config(config)
        access_profiles = AccessProfiles.from_config(config)
        rule_engine = PermissionRuleEngine.from_config(config)
        template_store = TemplateStore.from_config(config)

        connection_id = payload.get("connection_profile_id") or config["active_connection_profile_id"]
        access_id = payload.get("access_profile_id") or config["active_access_profile_id"]

        connection_profile = connection_profiles.get(connection_id)
        access_profile = access_profiles.get(access_id)

        if access_profile.connection_profile_id != connection_profile.id:
            raise AuthorizationError(
                "Access profile is not bound to the selected connection profile",
                {
                    "access_profile_id": access_profile.id,
                    "connection_profile_id": connection_profile.id,
                },
            )

        secret = SecretService("odoo-plugin").get_secret(connection_profile.secret_ref)
        client = OdooClient(
            url=connection_profile.base_url,
            port=connection_profile.port,
            database=connection_profile.database,
            login=connection_profile.login,
            password=secret,
        )

        if action == "odoo_read":
            return self._execute_read(action, model, payload, config, access_profile, connection_profile, rule_engine, client)
        if action == "odoo_create":
            if config.get("read_only", True):
                raise AuthorizationError("Global read-only mode is enabled")
            return self._execute_create(action, model, payload, config, access_profile, connection_profile, rule_engine, client, template_store)
        if action == "odoo_write":
            if config.get("read_only", True):
                raise AuthorizationError("Global read-only mode is enabled")
            return self._execute_write(action, model, payload, config, access_profile, connection_profile, rule_engine, client)
        if action == "odoo_delete":
            if config.get("read_only", True):
                raise AuthorizationError("Global read-only mode is enabled")
            return self._execute_delete(action, model, payload, config, access_profile, connection_profile, rule_engine, client)
        if action == "odoo_list_models":
            return self._execute_list_models(client, config, access_profile, connection_profile)
        if action == "odoo_list_fields":
            return self._execute_list_fields(model, client, config, access_profile, connection_profile)
        if action == "odoo_rollback":
            return self._execute_rollback(payload, client)

        raise AuthorizationError("Unsupported action", {"action": action})

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def _execute_read(self, action, model, payload, config, access_profile, connection_profile, rule_engine, client):
        requested_fields: list[str] = payload.get("fields") or ["id", "name"]
        domain: list[Any] = payload.get("domain") or []
        limit: int = payload.get("limit") or config.get("default_limit", 25)

        decision = rule_engine.evaluate(
            access_profile_id=access_profile.id,
            model=model,
            operation="read",
            fields=requested_fields,
            default_confirmation=access_profile.default_read_confirmation,
        )
        if not decision.allowed:
            raise AuthorizationError("Read denied by policy", {"decision": decision.__dict__})

        allowed_fields = [
            f for f in requested_fields
            if rule_engine.is_field_allowed(
                access_profile_id=access_profile.id, model=model, operation="read", field=f,
            )
        ]
        if not allowed_fields:
            raise AuthorizationError("No readable fields allowed for this model",
                                     {"model": model, "requested": requested_fields})

        entry = self.action_log.start(
            action=action, model=model, operation="read",
            access_profile_id=access_profile.id, connection_profile_id=connection_profile.id,
            request={"domain": domain, "fields": allowed_fields, "limit": limit},
            metadata={"decision": decision.__dict__},
        )
        try:
            records = client.get(model, domain, allowed_fields, limit)
            result = {"records": records, "count": len(records), "decision": decision.__dict__}
            self.action_log.mark_success(entry, result)
            return {"ok": True, **result}
        except Exception as exc:
            self.action_log.mark_error(entry, {"message": str(exc)})
            raise

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def _execute_create(self, action, model, payload, config, access_profile, connection_profile, rule_engine, client, template_store):
        template_id: str | None = payload.get("template_id")
        if template_id:
            template = template_store.get(template_id)
            values = template.render(payload.get("variables", {}))
        else:
            values: dict[str, Any] = payload.get("values", {})

        if not values:
            raise ValidationError("No values provided for create", {"model": model})

        decision = rule_engine.evaluate(
            access_profile_id=access_profile.id, model=model, operation="create",
            fields=list(values.keys()), default_confirmation=access_profile.default_create_confirmation,
        )
        if not decision.allowed:
            raise AuthorizationError("Create denied by policy", {"decision": decision.__dict__})

        if decision.require_confirmation and not payload.get("confirmed", False):
            raise ConfirmationRequiredError(
                "Create requires explicit confirmation",
                {"model": model, "fields": list(values.keys()), "decision": decision.__dict__},
            )

        allowed_values = {
            k: v for k, v in values.items()
            if rule_engine.is_field_allowed(
                access_profile_id=access_profile.id, model=model, operation="create", field=k,
            )
        }

        entry = self.action_log.start(
            action=action, model=model, operation="create",
            access_profile_id=access_profile.id, connection_profile_id=connection_profile.id,
            request={"values": allowed_values},
            metadata={
                "decision": decision.__dict__,
                "reversibility": self.rollback_service.get_reversibility("create").__dict__,
            },
        )
        snapshot = self.snapshot_store.create(
            action_log_id=entry.id, model=model, operation="create",
            record_ids=[], state_before={"note": "no previous record — create operation"},
        )
        try:
            record_id = client.post(model, allowed_values)
            result = {
                "record_id": record_id, "snapshot_id": snapshot.id,
                "decision": decision.__dict__,
                "reversibility": self.rollback_service.get_reversibility("create").__dict__,
            }
            self.action_log.mark_success(entry, result)
            return {"ok": True, **result}
        except Exception as exc:
            self.action_log.mark_error(entry, {"message": str(exc)})
            raise

    # ------------------------------------------------------------------
    # WRITE
    # ------------------------------------------------------------------

    def _execute_write(self, action, model, payload, config, access_profile, connection_profile, rule_engine, client):
        record_ids: list[int] = payload.get("ids", [])
        values: dict[str, Any] = payload.get("values", {})

        if not record_ids:
            raise ValidationError("No record ids provided for write", {"model": model})
        if not values:
            raise ValidationError("No values provided for write", {"model": model})

        decision = rule_engine.evaluate(
            access_profile_id=access_profile.id, model=model, operation="write",
            fields=list(values.keys()), default_confirmation=access_profile.default_write_confirmation,
        )
        if not decision.allowed:
            raise AuthorizationError("Write denied by policy", {"decision": decision.__dict__})

        if decision.require_confirmation and not payload.get("confirmed", False):
            raise ConfirmationRequiredError(
                "Write requires explicit confirmation",
                {"model": model, "ids": record_ids, "decision": decision.__dict__},
            )

        allowed_values = {
            k: v for k, v in values.items()
            if rule_engine.is_field_allowed(
                access_profile_id=access_profile.id, model=model, operation="write", field=k,
            )
        }

        try:
            state_before = client.get(model, [["id", "in", record_ids]], list(allowed_values.keys()), len(record_ids))
        except Exception:
            state_before = {"note": "could not snapshot pre-write state"}

        entry = self.action_log.start(
            action=action, model=model, operation="write",
            access_profile_id=access_profile.id, connection_profile_id=connection_profile.id,
            request={"ids": record_ids, "values": allowed_values},
            metadata={
                "decision": decision.__dict__,
                "reversibility": self.rollback_service.get_reversibility("write").__dict__,
            },
        )
        snapshot = self.snapshot_store.create(
            action_log_id=entry.id, model=model, operation="write",
            record_ids=record_ids, state_before={"records": state_before},
        )
        try:
            success = client.put(model, record_ids, allowed_values)
            result = {
                "success": success, "updated_ids": record_ids,
                "snapshot_id": snapshot.id, "decision": decision.__dict__,
                "reversibility": self.rollback_service.get_reversibility("write").__dict__,
            }
            self.action_log.mark_success(entry, result)
            return {"ok": True, **result}
        except Exception as exc:
            self.action_log.mark_error(entry, {"message": str(exc)})
            raise

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def _execute_delete(self, action, model, payload, config, access_profile, connection_profile, rule_engine, client):
        record_ids: list[int] = payload.get("ids", [])
        if not record_ids:
            raise ValidationError("No record ids provided for delete", {"model": model})

        decision = rule_engine.evaluate(
            access_profile_id=access_profile.id, model=model, operation="delete",
            fields=["*"], default_confirmation=access_profile.default_delete_confirmation,
        )
        if not decision.allowed:
            raise AuthorizationError("Delete denied by policy", {"decision": decision.__dict__})

        if decision.require_confirmation and not payload.get("confirmed", False):
            raise ConfirmationRequiredError(
                "Delete requires explicit confirmation",
                {"model": model, "ids": record_ids, "decision": decision.__dict__},
            )

        try:
            state_before = client.get(model, [["id", "in", record_ids]], ["id", "name"], len(record_ids))
        except Exception:
            state_before = {"note": "could not snapshot pre-delete state"}

        entry = self.action_log.start(
            action=action, model=model, operation="delete",
            access_profile_id=access_profile.id, connection_profile_id=connection_profile.id,
            request={"ids": record_ids},
            metadata={
                "decision": decision.__dict__,
                "reversibility": self.rollback_service.get_reversibility("delete").__dict__,
            },
        )
        snapshot = self.snapshot_store.create(
            action_log_id=entry.id, model=model, operation="delete",
            record_ids=record_ids, state_before={"records": state_before},
        )
        try:
            success = client.delete(model, record_ids)
            result = {
                "success": success, "deleted_ids": record_ids,
                "snapshot_id": snapshot.id, "decision": decision.__dict__,
                "reversibility": self.rollback_service.get_reversibility("delete").__dict__,
            }
            self.action_log.mark_success(entry, result)
            return {"ok": True, **result}
        except Exception as exc:
            self.action_log.mark_error(entry, {"message": str(exc)})
            raise

    # ------------------------------------------------------------------
    # META — list models / fields (UI selectors)
    # ------------------------------------------------------------------

    def _execute_list_models(self, client, config, access_profile, connection_profile):
        """Return all Odoo models. Admin tool — not filtered by permission rules."""
        try:
            ir_model = client.get_model("ir.model")
            models = ir_model.search_read([], ["model", "name", "info"], order="model asc")
            return {
                "ok": True,
                "models": [
                    {"model": m["model"], "name": m.get("name", ""), "info": m.get("info", "")}
                    for m in models
                ],
                "count": len(models),
            }
        except Exception as exc:
            from .errors import ServiceError
            raise ServiceError(f"Unable to list models: {exc}") from exc

    def _execute_list_fields(self, model, client, config, access_profile, connection_profile):
        """Return all fields of a model with type metadata. Used by UI selectors."""
        try:
            metadata = self.metadata_service.get_fields_metadata(
                client=client, profile_id=access_profile.id, model_name=model,
            )
            fields = [
                {
                    "name": fname,
                    "label": fmeta.get("string", fname),
                    "type": fmeta.get("type", "unknown"),
                    "required": fmeta.get("required", False),
                    "readonly": fmeta.get("readonly", False),
                    "relation": fmeta.get("relation"),
                }
                for fname, fmeta in metadata.items()
            ]
            return {"ok": True, "model": model, "fields": fields, "count": len(fields)}
        except Exception as exc:
            from .errors import ServiceError
            raise ServiceError(f"Unable to list fields for '{model}': {exc}") from exc

    # ------------------------------------------------------------------
    # ROLLBACK
    # ------------------------------------------------------------------

    def _execute_rollback(self, payload, client):
        snapshot_id: str | None = payload.get("snapshot_id")
        action_log_id: str | None = payload.get("action_log_id")
        snapshot = None
        if snapshot_id:
            snapshot = self.snapshot_store.get(snapshot_id)
        elif action_log_id:
            snapshot = self.snapshot_store.get_by_action_log(action_log_id)
        if snapshot is None:
            from .errors import NotFoundError
            raise NotFoundError("Snapshot not found",
                                {"snapshot_id": snapshot_id, "action_log_id": action_log_id})
        return self.rollback_service.attempt_rollback(snapshot, client)
