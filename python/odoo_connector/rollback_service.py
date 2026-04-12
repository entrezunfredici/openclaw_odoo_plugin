"""Rollback interface with honest stubbed execution."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .rollback_metadata import NOT_REVERSIBLE, REVERSIBILITY_BY_OPERATION, ReversibilityInfo
from .snapshot_store import Snapshot, SnapshotStore


class RollbackService:
    def __init__(self, snapshot_store: SnapshotStore) -> None:
        self._store = snapshot_store

    def get_reversibility(self, operation: str) -> ReversibilityInfo:
        return REVERSIBILITY_BY_OPERATION.get(
            operation,
            ReversibilityInfo(level=NOT_REVERSIBLE, note="Unknown operation."),
        )

    def attempt_rollback(self, snapshot: Snapshot, client: Any) -> dict[str, Any]:
        reversibility = self.get_reversibility(snapshot.operation)
        return {
            "ok": False,
            "rollback_requested": True,
            "rollback_executed": False,
            "status": "not_implemented",
            "snapshot_id": snapshot.id,
            "action_log_id": snapshot.action_log_id,
            "model": snapshot.model,
            "operation": snapshot.operation,
            "record_ids": snapshot.record_ids,
            "reversibility": asdict(reversibility),
            "reason": "Rollback execution is intentionally stubbed in this iteration.",
        }
