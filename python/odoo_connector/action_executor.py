"""Bounded action execution orchestrator."""

from __future__ import annotations

from typing import Any

from .access_profiles import AccessProfiles
from .action_log import ActionLogStore
from .connection_profiles import ConnectionProfiles
from .errors import AuthorizationError, ConfirmationRequiredError
from .odoo_client import OdooClient
from .permission_rules import PermissionRuleEngine
from .rollback_service import RollbackService
from .secret_service import SecretService
from .snapshot_store import SnapshotStore
from .templates import TemplateStore
from .validators import validate_action_payload, validate_config
from .odoo_client import OdooClient



class ActionExecutor:
    """Coordinates validation, authorization, snapshotting, logging, and execution."""

    def __init__(self) -> None:
        self.action_log = ActionLogStore()
        self.snapshot_store = SnapshotStore()
        self.rollback_service = RollbackService(self.snapshot_store)

    def execute(self, client, model, action: str, payload: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        validate_config(config)
        validate_action_payload(client, model, action, payload)

        connection_profiles = ConnectionProfiles.from_config(config)
        access_profiles = AccessProfiles.from_config(config)
        rule_engine = PermissionRuleEngine.from_config(config)
        _template_store = TemplateStore.from_config(config)

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

        if action == "list_tasks":
            return self._execute_list_tasks(
                payload,
                config,
                access_profile_id=access_profile.id,
                connection_profile_id=connection_profile.id,
                rule_engine=rule_engine,
                client=client,
            )

        if action == "create_task":
            if config.get("read_only", True):
                raise AuthorizationError("Global read-only mode is enabled")

            return self._execute_create_task(
                payload,
                access_profile_id=access_profile.id,
                connection_profile_id=connection_profile.id,
                rule_engine=rule_engine,
                client=client,
                default_confirmation=access_profile.default_create_confirmation,
            )

        raise AuthorizationError("Unsupported bounded action", {"action": action})

    def _execute_list_tasks(
        self,
        payload: dict[str, Any],
        config: dict[str, Any],
        access_profile_id: str,
        connection_profile_id: str,
        rule_engine: PermissionRuleEngine,
        client: OdooClient,
    ) -> dict[str, Any]:
        fields = ["id", "name", "stage_id", "project_id"]
        decision = rule_engine.evaluate(
            access_profile_id=access_profile_id,
            model=READ_MODEL,
            operation="read",
            fields=fields,
            default_confirmation=False,
        )
        if not decision.allowed:
            raise AuthorizationError("Read is not allowed", {"decision": decision.__dict__})

        entry = self.action_log.start(
            action="list_tasks",
            model=READ_MODEL,
            operation="read",
            access_profile_id=access_profile_id,
            connection_profile_id=connection_profile_id,
            request={"project_id": payload["project_id"], "limit": payload.get("limit")},
            metadata={"decision": decision.__dict__},
        )

        result = {
            "tasks": client.get(
                READ_MODEL,
                [["project_id", "=", payload["project_id"]]],
                fields,
                payload.get("limit", config.get("default_limit", 25)),
            ),
            "decision": decision.__dict__,
        }
        self.action_log.mark_success(entry, result)
        return {"ok": True, **result}

    def _execute_create_task(
        self,
        payload: dict[str, Any],
        access_profile_id: str,
        connection_profile_id: str,
        rule_engine: PermissionRuleEngine,
        client: OdooClient,
        default_confirmation: bool,
    ) -> dict[str, Any]:
        values = {
            "project_id": payload["project_id"],
            "name": payload["name"],
            "description": payload.get("description", ""),
        }
        decision = rule_engine.evaluate(
            access_profile_id=access_profile_id,
            model=WRITE_MODEL,
            operation="create",
            fields=list(values.keys()),
            default_confirmation=default_confirmation,
        )
        if not decision.allowed:
            raise AuthorizationError("Create is not allowed", {"decision": decision.__dict__})

        if decision.require_confirmation and not payload.get("confirmed", False):
            raise ConfirmationRequiredError(
                "Create requires explicit confirmation",
                {"action": "create_task", "required": True, "decision": decision.__dict__},
            )

        entry = self.action_log.start(
            action="create_task",
            model=WRITE_MODEL,
            operation="create",
            access_profile_id=access_profile_id,
            connection_profile_id=connection_profile_id,
            request={"project_id": values["project_id"], "name": values["name"]},
            metadata={
                "decision": decision.__dict__,
                "reversibility": self.rollback_service.get_reversibility("create_task").__dict__,
            },
        )

        snapshot = self.snapshot_store.create(
            action_log_id=entry.id,
            model=WRITE_MODEL,
            operation="create",
            record_ids=[],
            state_before={"note": "create has no previous record"},
        )

        task_id = client.post(WRITE_MODEL, values)
        result = {
            "task_id": task_id,
            "snapshot_id": snapshot.id,
            "decision": decision.__dict__,
            "reversibility": self.rollback_service.get_reversibility("create_task").__dict__,
        }
        self.action_log.mark_success(entry, result)
        return {"ok": True, **result}
