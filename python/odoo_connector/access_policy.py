"""Backward-compatible access policy wrapper.

Prefer using PermissionRuleEngine directly via ActionExecutor.
"""

from __future__ import annotations

from .access_profiles import AccessProfile
from .permission_rules import PermissionDecision, PermissionRuleEngine


class OdooAccessPolicy:
    def __init__(self, engine: PermissionRuleEngine) -> None:
        self.engine = engine

    def evaluate(
        self,
        access_profile: AccessProfile,
        model: str,
        operation: str,
        fields: list[str],
    ) -> PermissionDecision:
        default_confirmation = access_profile.default_confirmation_for(operation)
        return self.engine.evaluate(
            access_profile_id=access_profile.id,
            model=model,
            operation=operation,
            fields=fields,
            default_confirmation=default_confirmation,
        )
