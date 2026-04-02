"""Snapshot storage for rollback attempts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class Snapshot:
    id: str
    action_log_id: str
    model: str
    operation: str
    record_ids: list[int]
    state_before: dict[str, Any]
    created_at_utc: str


class SnapshotStore:
    def __init__(self) -> None:
        self._snapshots: dict[str, Snapshot] = {}

    def create(
        self,
        action_log_id: str,
        model: str,
        operation: str,
        record_ids: list[int],
        state_before: dict[str, Any],
    ) -> Snapshot:
        snapshot = Snapshot(
            id=str(uuid4()),
            action_log_id=action_log_id,
            model=model,
            operation=operation,
            record_ids=record_ids,
            state_before=state_before,
            created_at_utc=datetime.now(tz=UTC).isoformat(),
        )
        self._snapshots[snapshot.id] = snapshot
        return snapshot

    def get(self, snapshot_id: str) -> Snapshot | None:
        return self._snapshots.get(snapshot_id)
