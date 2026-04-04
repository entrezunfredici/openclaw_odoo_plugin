"""Rollback service — best-effort, honest about reversibility limits."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .snapshot_store import Snapshot, SnapshotStore


@dataclass(slots=True)
class ReversibilityInfo:
    level: str  # FULLY_REVERSIBLE | PARTIALLY_REVERSIBLE | NOT_REVERSIBLE
    note: str


_REVERSIBILITY: dict[str, ReversibilityInfo] = {
    "create": ReversibilityInfo(
        level="FULLY_REVERSIBLE",
        note="Record can be deleted to undo the create.",
    ),
    "write": ReversibilityInfo(
        level="FULLY_REVERSIBLE",
        note="Previous values were snapshotted and can be restored.",
    ),
    "delete": ReversibilityInfo(
        level="NOT_REVERSIBLE",
        note="Deleted records cannot be recovered via this plugin.",
    ),
}


class RollbackService:
    def __init__(self, snapshot_store: SnapshotStore) -> None:
        self._store = snapshot_store

    def get_reversibility(self, operation: str) -> ReversibilityInfo:
        return _REVERSIBILITY.get(
            operation,
            ReversibilityInfo(level="NOT_REVERSIBLE", note="Unknown operation."),
        )

    def attempt_rollback(self, snapshot: Snapshot, client: Any) -> dict[str, Any]:
        """Attempt to roll back using snapshot state_before."""
        operation = snapshot.operation

        if operation == "create":
            # Roll back a create → delete the created record
            if not snapshot.record_ids:
                return {
                    "ok": False,
                    "rollback_attempted": True,
                    "reason": "No record ids in snapshot — cannot roll back create without the created id.",
                }
            try:
                client.delete(snapshot.model, snapshot.record_ids)
                return {"ok": True, "rollback_attempted": True, "deleted_ids": snapshot.record_ids}
            except Exception as exc:
                return {"ok": False, "rollback_attempted": True, "reason": str(exc)}

        if operation == "write":
            records_before = snapshot.state_before.get("records", [])
            if not records_before or not isinstance(records_before, list):
                return {
                    "ok": False,
                    "rollback_attempted": True,
                    "reason": "No valid pre-write state in snapshot.",
                }
            errors = []
            for record in records_before:
                rid = record.get("id")
                restore_values = {k: v for k, v in record.items() if k != "id"}
                if rid and restore_values:
                    try:
                        client.put(snapshot.model, [rid], restore_values)
                    except Exception as exc:
                        errors.append({"id": rid, "error": str(exc)})
            if errors:
                return {"ok": False, "rollback_attempted": True, "errors": errors}
            return {"ok": True, "rollback_attempted": True, "restored_ids": snapshot.record_ids}

        # delete → NOT_REVERSIBLE
        return {
            "ok": False,
            "rollback_attempted": False,
            "reason": f"Operation '{operation}' is not reversible.",
        }
