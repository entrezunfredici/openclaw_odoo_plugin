"""Rollback interfaces and conservative rollback behavior."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ServiceError
from .snapshot_store import SnapshotStore

FULLY_REVERSIBLE = "FULLY_REVERSIBLE"
PARTIALLY_REVERSIBLE = "PARTIALLY_REVERSIBLE"
NOT_REVERSIBLE = "NOT_REVERSIBLE"


@dataclass(slots=True)
class ActionReversibility:
    action: str
    level: str
    reason: str


class RollbackService:
    def __init__(self, snapshot_store: SnapshotStore) -> None:
        self.snapshot_store = snapshot_store
        self._reversibility = {
            "list_tasks": ActionReversibility(
                action="list_tasks",
                level=NOT_REVERSIBLE,
                reason="Read actions do not need rollback",
            ),
            "create_task": ActionReversibility(
                action="create_task",
                level=PARTIALLY_REVERSIBLE,
                reason="Created task can often be archived manually, not guaranteed reversible",
            ),
        }

    def get_reversibility(self, action: str) -> ActionReversibility:
        return self._reversibility.get(
            action,
            ActionReversibility(
                action=action,
                level=NOT_REVERSIBLE,
                reason="Action has no rollback strategy",
            ),
        )

    def rollback_action(self, action_log_id: str, snapshot_id: str) -> dict:
        snapshot = self.snapshot_store.get(snapshot_id)
        if snapshot is None:
            raise ServiceError(
                "Rollback snapshot not found",
                {"action_log_id": action_log_id, "snapshot_id": snapshot_id},
            )

        return {
            "ok": False,
            "status": "not_implemented",
            "message": "Rollback execution is not implemented yet",
            "action_log_id": action_log_id,
            "snapshot_id": snapshot_id,
        }
