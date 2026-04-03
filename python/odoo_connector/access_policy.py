"""Backward-compatible access policy wrapper.

Prefer using PermissionRuleEngine directly via ActionExecutor.
"""

from __future__ import annotations

from .access_profiles import AccessProfile
from .permission_rules import PermissionDecision, PermissionRuleEngine
from typing import Any


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

class AccessPolicy:
    def __init__(self, permission_rules: list[dict[str, Any]]) -> None:
        self.permission_rules = permission_rules

    def is_field_allowed(
        self,
        *,
        access_profile_id: str,
        model_name: str,
        field_name: str,
        operation: str,
    ) -> bool:
        matching_rules: list[dict[str, Any]] = []

        for rule in self.permission_rules:
            if rule["access_profile_id"] != access_profile_id:
                continue
            if rule["model"] != model_name:
                continue
            if rule["operation"] != operation:
                continue
            if rule["field"] not in {field_name, "*"}:
                continue
            matching_rules.append(rule)

        if not matching_rules:
            return False

        # Priority:
        # 1. explicit field rule before wildcard
        # 2. deny before allow
        matching_rules.sort(
            key=lambda r: (
                0 if r["field"] == field_name else 1,
                0 if r["allowed"] is False else 1,
            )
        )

        selected = matching_rules[0]
        return bool(selected["allowed"])

    def requires_confirmation(
        self,
        *,
        access_profile_id: str,
        model_name: str,
        field_names: list[str],
        operation: str,
    ) -> bool:
        for field_name in field_names:
            matching_rules: list[dict[str, Any]] = []

            for rule in self.permission_rules:
                if rule["access_profile_id"] != access_profile_id:
                    continue
                if rule["model"] != model_name:
                    continue
                if rule["operation"] != operation:
                    continue
                if rule["field"] not in {field_name, "*"}:
                    continue
                matching_rules.append(rule)

            matching_rules.sort(
                key=lambda r: (
                    0 if r["field"] == field_name else 1,
                    0 if r["allowed"] is False else 1,
                )
            )

            if matching_rules and matching_rules[0].get("require_confirmation", False):
                return True

        return False
