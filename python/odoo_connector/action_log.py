"""In-memory action log storage for auditability."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class ActionLogEntry:
    id: str
    timestamp_utc: str
    action: str
    model: str
    operation: str
    status: str
    access_profile_id: str
    connection_profile_id: str
    request: dict[str, Any]
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ActionLogStore:
    def __init__(self) -> None:
        self._entries: list[ActionLogEntry] = []

    def start(
        self,
        action: str,
        model: str,
        operation: str,
        access_profile_id: str,
        connection_profile_id: str,
        request: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> ActionLogEntry:
        entry = ActionLogEntry(
            id=str(uuid4()),
            timestamp_utc=datetime.now(tz=UTC).isoformat(),
            action=action,
            model=model,
            operation=operation,
            status="started",
            access_profile_id=access_profile_id,
            connection_profile_id=connection_profile_id,
            request=request,
            metadata=metadata or {},
        )
        self._entries.append(entry)
        return entry

    def mark_success(self, entry: ActionLogEntry, result: dict[str, Any]) -> None:
        entry.status = "succeeded"
        entry.result = result

    def mark_error(self, entry: ActionLogEntry, error: dict[str, Any]) -> None:
        entry.status = "failed"
        entry.error = error

    def list_entries(self) -> list[ActionLogEntry]:
        return list(self._entries)
