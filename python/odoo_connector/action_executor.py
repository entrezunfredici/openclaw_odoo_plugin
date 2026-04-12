"""Generic action executor with deny-by-default policy enforcement."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .access_profiles import AccessProfile, AccessProfiles
from .action_log import ActionLogStore
from .connection_profiles import ConnectionProfile, ConnectionProfiles
from .errors import AuthorizationError, ConfirmationRequiredError, NotFoundError, ValidationError
from .model_metadata_service import ModelMetadataService
from .odoo_client import OdooClient
from .permission_rules import PermissionRuleEngine
from .rollback_service import RollbackService
from .secret_service import SecretService
from .snapshot_store import SnapshotStore
from .templates import Template, TemplateStore
from .validators import validate_action_payload, validate_config, validate_create_values_for_model


def _to_serializable_dict(value: Any) -> dict[str, Any]:
    return asdict(value)


class ActionExecutor:
    """Coordinates validation, authorization, snapshots, logging, and execution."""

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
        validate_action_payload(action, payload, model)

        connection_profiles = ConnectionProfiles.from_config(config)
        access_profiles = AccessProfiles.from_config(config)
        rule_engine = PermissionRuleEngine.from_config(config)
        template_store = TemplateStore.from_config(config)

        connection_id = payload.get("connection_profile_id") or config["active_connection_profile_id"]
        access_id = payload.get("access_profile_id") or config["active_access_profile_id"]

        connection_profile = connection_profiles.get(connection_id)
        access_profile = access_profiles.get(access_id)
        self._validate_profile_binding(connection_profile, access_profile)

        secret = SecretService("odoo-plugin").get_secret(connection_profile.secret_ref)
        client = OdooClient(
            url=connection_profile.base_url,
            port=connection_profile.port,
            database=connection_profile.database,
            login=connection_profile.login,
            password=secret,
        )

        if action == "odoo_read":
            return self._execute_read(model, payload, config, access_profile, connection_profile, rule_engine, client)
        if action == "odoo_create":
            self._ensure_writes_enabled(config)
            return self._execute_create(model, payload, access_profile, connection_profile, rule_engine, client, template_store)
        if action in {"odoo_update", "odoo_write"}:
            self._ensure_writes_enabled(config)
            return self._execute_update(action, model, payload, access_profile, connection_profile, rule_engine, client)
        if action == "odoo_delete":
            self._ensure_writes_enabled(config)
            return self._execute_delete(model, payload, access_profile, connection_profile, rule_engine, client)
        if action == "odoo_list_models":
            return self._execute_list_models(client)
        if action == "odoo_list_fields":
            return self._execute_list_fields(model, client, access_profile)
        if action == "odoo_rollback":
            return self._execute_rollback(payload, client)

        raise AuthorizationError("Unsupported action", {"action": action})

    @staticmethod
    def _ensure_writes_enabled(config: dict[str, Any]) -> None:
        if config.get("read_only", True):
            raise AuthorizationError("Global read-only mode is enabled")

    @staticmethod
    def _validate_profile_binding(connection_profile: ConnectionProfile, access_profile: AccessProfile) -> None:
        if access_profile.connection_profile_id != connection_profile.id:
            raise AuthorizationError(
                "Access profile is not bound to the selected connection profile",
                {
                    "access_profile_id": access_profile.id,
                    "connection_profile_id": connection_profile.id,
                },
            )

    def _resolve_create_values(
        self,
        *,
        model: str,
        payload: dict[str, Any],
        template_store: TemplateStore,
    ) -> tuple[dict[str, Any], Template | None]:
        template_id = payload.get("template_id")
        if not template_id:
            values = payload.get("values", {})
            return values, None

        template = template_store.get(template_id)
        if template.action != "create_task":
            raise ValidationError(
                "Unsupported template action",
                {"template_id": template.id, "action": template.action},
            )
        if model != "project.task":
            raise ValidationError(
                "Template 'create_task' can only be used with model 'project.task'",
                {"template_id": template.id, "model": model},
            )

        values = template.render(payload.get("variables", {}))
        return values, template

    def _execute_read(
        self,
        model: str,
        payload: dict[str, Any],
        config: dict[str, Any],
        access_profile: AccessProfile,
        connection_profile: ConnectionProfile,
        rule_engine: PermissionRuleEngine,
        client: OdooClient,
    ) -> dict[str, Any]:
        requested_fields: list[str] = payload.get("fields") or ["id", "name"]
        filters: list[Any] = payload.get("filters") or payload.get("domain") or []
        limit: int = payload.get("limit") or config.get("default_limit", 25)

        decision = rule_engine.evaluate(
            access_profile_id=access_profile.id,
            model=model,
            operation="read",
            fields=requested_fields,
            default_confirmation=access_profile.default_read_confirmation,
        )
        if not decision.allowed:
            raise AuthorizationError("Read denied by policy", {"decision": _to_serializable_dict(decision)})

        allowed_fields = [
            field
            for field in requested_fields
            if rule_engine.is_field_allowed(
                access_profile_id=access_profile.id,
                model=model,
                operation="read",
                field=field,
            )
        ]
        if not allowed_fields:
            raise AuthorizationError(
                "No readable fields allowed for this model",
                {"model": model, "requested": requested_fields},
            )

        entry = self.action_log.start(
            action="odoo_read",
            model=model,
            operation="read",
            access_profile_id=access_profile.id,
            connection_profile_id=connection_profile.id,
            request={"filters": filters, "fields": allowed_fields, "limit": limit},
            metadata={"decision": _to_serializable_dict(decision)},
        )
        try:
            records = client.get(model, filters, allowed_fields, limit)
            result = {"records": records, "count": len(records), "decision": _to_serializable_dict(decision)}
            self.action_log.mark_success(entry, result)
            return {"ok": True, **result}
        except Exception as exc:
            self.action_log.mark_error(entry, {"message": str(exc)})
            raise

    def _execute_create(
        self,
        model: str,
        payload: dict[str, Any],
        access_profile: AccessProfile,
        connection_profile: ConnectionProfile,
        rule_engine: PermissionRuleEngine,
        client: OdooClient,
        template_store: TemplateStore,
    ) -> dict[str, Any]:
        values, template = self._resolve_create_values(model=model, payload=payload, template_store=template_store)
        template_id = template.id if template else None

        validate_create_values_for_model(
            model=model,
            values=values,
            template_action=template.action if template else None,
        )

        decision = rule_engine.evaluate(
            access_profile_id=access_profile.id,
            model=model,
            operation="create",
            fields=list(values.keys()),
            default_confirmation=access_profile.default_create_confirmation,
            template_id=template_id,
        )
        if not decision.allowed:
            raise AuthorizationError("Create denied by policy", {"decision": _to_serializable_dict(decision)})

        if decision.require_confirmation and not payload.get("confirmed", False):
            raise ConfirmationRequiredError(
                "Create requires explicit confirmation",
                {
                    "model": model,
                    "fields": list(values.keys()),
                    "decision": _to_serializable_dict(decision),
                },
            )

        allowed_values = {
            field: value
            for field, value in values.items()
            if rule_engine.is_field_allowed(
                access_profile_id=access_profile.id,
                model=model,
                operation="create",
                field=field,
                template_id=template_id,
            )
        }
        if not allowed_values:
            raise AuthorizationError("No creatable fields allowed for this request", {"model": model})

        reversibility = _to_serializable_dict(self.rollback_service.get_reversibility("create"))
        entry = self.action_log.start(
            action="odoo_create",
            model=model,
            operation="create",
            access_profile_id=access_profile.id,
            connection_profile_id=connection_profile.id,
            request={
                "values": allowed_values,
                "template_id": template_id,
            },
            metadata={
                "decision": _to_serializable_dict(decision),
                "reversibility": reversibility,
            },
        )
        snapshot = self.snapshot_store.create(
            action_log_id=entry.id,
            model=model,
            operation="create",
            record_ids=[],
            state_before={"note": "No previous record exists before create."},
        )
        try:
            record_id = client.post(model, allowed_values)
            self.snapshot_store.attach_record_ids(snapshot.id, [record_id])
            result = {
                "record_id": record_id,
                "snapshot_id": snapshot.id,
                "decision": _to_serializable_dict(decision),
                "reversibility": reversibility,
            }
            self.action_log.mark_success(entry, result)
            return {"ok": True, **result}
        except Exception as exc:
            self.action_log.mark_error(entry, {"message": str(exc)})
            raise

    def _execute_update(
        self,
        action: str,
        model: str,
        payload: dict[str, Any],
        access_profile: AccessProfile,
        connection_profile: ConnectionProfile,
        rule_engine: PermissionRuleEngine,
        client: OdooClient,
    ) -> dict[str, Any]:
        record_ids = [payload["id"]] if "id" in payload else payload.get("ids", [])
        values: dict[str, Any] = payload.get("values", {})

        decision = rule_engine.evaluate(
            access_profile_id=access_profile.id,
            model=model,
            operation="write",
            fields=list(values.keys()),
            default_confirmation=access_profile.default_write_confirmation,
        )
        if not decision.allowed:
            raise AuthorizationError("Update denied by policy", {"decision": _to_serializable_dict(decision)})

        if decision.require_confirmation and not payload.get("confirmed", False):
            raise ConfirmationRequiredError(
                "Update requires explicit confirmation",
                {"model": model, "ids": record_ids, "decision": _to_serializable_dict(decision)},
            )

        allowed_values = {
            field: value
            for field, value in values.items()
            if rule_engine.is_field_allowed(
                access_profile_id=access_profile.id,
                model=model,
                operation="write",
                field=field,
            )
        }
        if not allowed_values:
            raise AuthorizationError("No writable fields allowed for this request", {"model": model})

        try:
            state_before = client.get(model, [["id", "in", record_ids]], ["id", *allowed_values.keys()], len(record_ids))
        except Exception:
            state_before = {"note": "Could not snapshot pre-update state."}

        reversibility = _to_serializable_dict(self.rollback_service.get_reversibility("write"))
        entry = self.action_log.start(
            action=action,
            model=model,
            operation="write",
            access_profile_id=access_profile.id,
            connection_profile_id=connection_profile.id,
            request={"ids": record_ids, "values": allowed_values},
            metadata={
                "decision": _to_serializable_dict(decision),
                "reversibility": reversibility,
            },
        )
        snapshot = self.snapshot_store.create(
            action_log_id=entry.id,
            model=model,
            operation="write",
            record_ids=record_ids,
            state_before={"records": state_before},
        )
        try:
            success = client.put(model, record_ids, allowed_values)
            result = {
                "success": success,
                "updated_ids": record_ids,
                "snapshot_id": snapshot.id,
                "decision": _to_serializable_dict(decision),
                "reversibility": reversibility,
            }
            self.action_log.mark_success(entry, result)
            return {"ok": True, **result}
        except Exception as exc:
            self.action_log.mark_error(entry, {"message": str(exc)})
            raise

    def _execute_delete(
        self,
        model: str,
        payload: dict[str, Any],
        access_profile: AccessProfile,
        connection_profile: ConnectionProfile,
        rule_engine: PermissionRuleEngine,
        client: OdooClient,
    ) -> dict[str, Any]:
        record_ids = [payload["id"]] if "id" in payload else payload.get("ids", [])

        decision = rule_engine.evaluate(
            access_profile_id=access_profile.id,
            model=model,
            operation="delete",
            fields=["*"],
            default_confirmation=access_profile.default_delete_confirmation,
        )
        if not decision.allowed:
            raise AuthorizationError("Delete denied by policy", {"decision": _to_serializable_dict(decision)})

        if decision.require_confirmation and not payload.get("confirmed", False):
            raise ConfirmationRequiredError(
                "Delete requires explicit confirmation",
                {"model": model, "ids": record_ids, "decision": _to_serializable_dict(decision)},
            )

        try:
            state_before = client.get(model, [["id", "in", record_ids]], ["id", "name"], len(record_ids))
        except Exception:
            state_before = {"note": "Could not snapshot pre-delete state."}

        reversibility = _to_serializable_dict(self.rollback_service.get_reversibility("delete"))
        entry = self.action_log.start(
            action="odoo_delete",
            model=model,
            operation="delete",
            access_profile_id=access_profile.id,
            connection_profile_id=connection_profile.id,
            request={"ids": record_ids},
            metadata={
                "decision": _to_serializable_dict(decision),
                "reversibility": reversibility,
            },
        )
        snapshot = self.snapshot_store.create(
            action_log_id=entry.id,
            model=model,
            operation="delete",
            record_ids=record_ids,
            state_before={"records": state_before},
        )
        try:
            success = client.delete(model, record_ids)
            result = {
                "success": success,
                "deleted_ids": record_ids,
                "snapshot_id": snapshot.id,
                "decision": _to_serializable_dict(decision),
                "reversibility": reversibility,
            }
            self.action_log.mark_success(entry, result)
            return {"ok": True, **result}
        except Exception as exc:
            self.action_log.mark_error(entry, {"message": str(exc)})
            raise

    def _execute_list_models(self, client: OdooClient) -> dict[str, Any]:
        try:
            ir_model = client.get_model("ir.model")
            models = ir_model.search_read([], ["model", "name", "info"], order="model asc")
            return {
                "ok": True,
                "models": [
                    {"model": item["model"], "name": item.get("name", ""), "info": item.get("info", "")}
                    for item in models
                ],
                "count": len(models),
            }
        except Exception as exc:
            raise ValidationError(f"Unable to list models: {exc}") from exc

    def _execute_list_fields(
        self,
        model: str,
        client: OdooClient,
        access_profile: AccessProfile,
    ) -> dict[str, Any]:
        try:
            metadata = self.metadata_service.get_fields_metadata(
                client=client,
                profile_id=access_profile.id,
                model_name=model,
            )
            fields = [
                {
                    "name": field_name,
                    "label": field_meta.get("string", field_name),
                    "type": field_meta.get("type", "unknown"),
                    "required": field_meta.get("required", False),
                    "readonly": field_meta.get("readonly", False),
                    "relation": field_meta.get("relation"),
                }
                for field_name, field_meta in metadata.items()
            ]
            return {"ok": True, "model": model, "fields": fields, "count": len(fields)}
        except Exception as exc:
            raise ValidationError(f"Unable to list fields for '{model}': {exc}") from exc

    def _execute_rollback(self, payload: dict[str, Any], client: OdooClient) -> dict[str, Any]:
        snapshot_id: str | None = payload.get("snapshot_id")
        action_log_id: str | None = payload.get("action_log_id")

        snapshot = None
        if snapshot_id:
            snapshot = self.snapshot_store.get(snapshot_id)
        elif action_log_id:
            snapshot = self.snapshot_store.get_by_action_log(action_log_id)

        if snapshot is None:
            raise NotFoundError(
                "Snapshot not found",
                {"snapshot_id": snapshot_id, "action_log_id": action_log_id},
            )

        return self.rollback_service.attempt_rollback(snapshot, client)
