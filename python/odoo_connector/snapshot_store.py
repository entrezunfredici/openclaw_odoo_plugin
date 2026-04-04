"""Snapshot store — records pre-action state for rollback support."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class Snapshot:
    id: str
    action_log_id: str
    timestamp_utc: str
    model: str
    operation: str
    record_ids: list[int]
    state_before: dict[str, Any]


class SnapshotStore:
    def __init__(self) -> None:
        self._snapshots: dict[str, Snapshot] = {}
        self._by_action_log: dict[str, str] = {}  # action_log_id -> snapshot_id

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
            timestamp_utc=datetime.now(tz=UTC).isoformat(),
            model=model,
            operation=operation,
            record_ids=record_ids,
            state_before=state_before,
        )
        self._snapshots[snapshot.id] = snapshot
        self._by_action_log[action_log_id] = snapshot.id
        return snapshot

    def get(self, snapshot_id: str) -> Snapshot | None:
        return self._snapshots.get(snapshot_id)

    def get_by_action_log(self, action_log_id: str) -> Snapshot | None:
        sid = self._by_action_log.get(action_log_id)
        return self._snapshots.get(sid) if sid else None

    def list_snapshots(self) -> list[Snapshot]:
        return list(self._snapshots.values())
