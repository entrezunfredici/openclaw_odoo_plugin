"""Rollback metadata separated from rollback execution."""

from __future__ import annotations

from dataclasses import dataclass


FULLY_REVERSIBLE = "FULLY_REVERSIBLE"
PARTIALLY_REVERSIBLE = "PARTIALLY_REVERSIBLE"
NOT_REVERSIBLE = "NOT_REVERSIBLE"


@dataclass(slots=True)
class ReversibilityInfo:
    level: str
    note: str


REVERSIBILITY_BY_OPERATION: dict[str, ReversibilityInfo] = {
    "create": ReversibilityInfo(
        level=FULLY_REVERSIBLE,
        note="A created record can be deleted, but rollback execution is not implemented yet.",
    ),
    "write": ReversibilityInfo(
        level=FULLY_REVERSIBLE,
        note="Previous values are snapshotted, but rollback execution is not implemented yet.",
    ),
    "delete": ReversibilityInfo(
        level=NOT_REVERSIBLE,
        note="Deleted records cannot be restored by this plugin.",
    ),
}
