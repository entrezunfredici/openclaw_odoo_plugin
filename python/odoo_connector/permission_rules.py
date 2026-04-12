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

    @staticmethod
    def _matches_template(rule: PermissionRule, template_id: str | None) -> bool:
        if not rule.template_ids:
            return template_id is None or isinstance(template_id, str)
        if template_id is None:
            return False
        return template_id in rule.template_ids

    def _matching_rules(
        self,
        *,
        access_profile_id: str,
        model: str,
        operation: str,
        field: str,
        template_id: str | None,
    ) -> list[PermissionRule]:
        return [
            rule
            for rule in self._rules
            if rule.access_profile_id == access_profile_id
            and rule.model == model
            and rule.operation == operation
            and (rule.field == field or rule.field == "*")
            and self._matches_template(rule, template_id)
        ]

    def is_field_allowed(
        self,
        *,
        access_profile_id: str,
        model: str,
        operation: str,
        field: str,
        template_id: str | None = None,
    ) -> bool:
        field_rules = self._matching_rules(
            access_profile_id=access_profile_id,
            model=model,
            operation=operation,
            field=field,
            template_id=template_id,
        )
        if not field_rules:
            return False

        field_rules.sort(key=lambda rule: (0 if rule.field == field else 1, 0 if not rule.allowed else 1))
        return bool(field_rules[0].allowed)

    def evaluate(
        self,
        access_profile_id: str,
        model: str,
        operation: str,
        fields: list[str],
        default_confirmation: bool,
        template_id: str | None = None,
    ) -> PermissionDecision:
        matched_rule_ids: list[str] = []
        require_confirmation = default_confirmation

        for field in fields:
            field_rules = self._matching_rules(
                access_profile_id=access_profile_id,
                model=model,
                operation=operation,
                field=field,
                template_id=template_id,
            )

            if not field_rules:
                template_details = {"template_id": template_id} if template_id else {}
                return PermissionDecision(
                    allowed=False,
                    require_confirmation=False,
                    matched_rule_ids=matched_rule_ids,
                    reason=(
                        "No rule matched "
                        f"(model={model}, field={field}, operation={operation}, {template_details})"
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

            field_rules.sort(key=lambda rule: (0 if rule.field == field else 1))
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
