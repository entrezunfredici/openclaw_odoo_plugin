"""Permission rules and deny-by-default authorization evaluation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PermissionRule:
    id: str
    access_profile_id: str
    model: str
    field: str
    operation: str
    allowed: bool
    require_confirmation: bool | None = None
    template_ids: list[str] | None = None


@dataclass(slots=True)
class PermissionDecision:
    allowed: bool
    require_confirmation: bool
    matched_rule_ids: list[str]
    reason: str


class PermissionRuleEngine:
    def __init__(self, rules: list[PermissionRule]) -> None:
        self._rules = rules

    @classmethod
    def from_config(cls, config: dict) -> "PermissionRuleEngine":
        raw_rules = config.get("permission_rules", [])
        return cls([PermissionRule(**item) for item in raw_rules])

    def evaluate(
        self,
        access_profile_id: str,
        model: str,
        operation: str,
        fields: list[str],
        default_confirmation: bool,
    ) -> PermissionDecision:
        matched_rule_ids: list[str] = []
        require_confirmation = default_confirmation

        for field in fields:
            field_rules = [
                rule
                for rule in self._rules
                if rule.access_profile_id == access_profile_id
                and rule.model == model
                and rule.operation == operation
                and (rule.field == field or rule.field == "*")
            ]

            if not field_rules:
                return PermissionDecision(
                    allowed=False,
                    require_confirmation=False,
                    matched_rule_ids=matched_rule_ids,
                    reason=(
                        f"No rule matched (model={model}, field={field}, operation={operation})"
                    ),
                )

            denying_rule = next((rule for rule in field_rules if not rule.allowed), None)
            if denying_rule is not None:
                matched_rule_ids.append(denying_rule.id)
                return PermissionDecision(
                    allowed=False,
                    require_confirmation=False,
                    matched_rule_ids=matched_rule_ids,
                    reason=f"Denied by rule '{denying_rule.id}'",
                )

            allow_rule = field_rules[0]
            matched_rule_ids.append(allow_rule.id)
            if allow_rule.require_confirmation is True:
                require_confirmation = True

        return PermissionDecision(
            allowed=True,
            require_confirmation=require_confirmation,
            matched_rule_ids=matched_rule_ids,
            reason="Allowed by explicit matching rules",
        )
