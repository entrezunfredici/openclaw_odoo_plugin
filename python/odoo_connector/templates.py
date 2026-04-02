"""Bounded action templates for safe payload generation."""

from __future__ import annotations

from dataclasses import dataclass
from string import Formatter
from typing import Any

from .errors import ValidationError

ALLOWED_TEMPLATE_ACTIONS = {"create_task"}


@dataclass(slots=True)
class Template:
    id: str
    label: str
    action: str
    required_variables: list[str]
    payload_template: dict[str, Any]
    enabled: bool


class TemplateStore:
    def __init__(self, templates: list[Template]) -> None:
        self._templates = {template.id: template for template in templates}

    @classmethod
    def from_config(cls, config: dict) -> "TemplateStore":
        raw_templates = config.get("templates", [])
        templates = [Template(**item) for item in raw_templates]
        return cls(templates)

    def preview(self, template_id: str, variables: dict[str, Any]) -> dict[str, Any]:
        template = self._templates.get(template_id)
        if template is None or not template.enabled:
            raise ValidationError("Template not found or disabled", {"template_id": template_id})
        if template.action not in ALLOWED_TEMPLATE_ACTIONS:
            raise ValidationError("Template action is not bounded", {"template_id": template_id})

        missing = [name for name in template.required_variables if name not in variables]
        if missing:
            raise ValidationError(
                "Template variables are missing",
                {"template_id": template_id, "missing_variables": missing},
            )

        return self._render_payload(template.payload_template, variables)

    def _render_payload(self, value: Any, variables: dict[str, Any]) -> Any:
        if isinstance(value, str):
            placeholders = [name for _, name, _, _ in Formatter().parse(value) if name]
            if placeholders:
                return value.format(**variables)
            return value
        if isinstance(value, list):
            return [self._render_payload(item, variables) for item in value]
        if isinstance(value, dict):
            return {key: self._render_payload(item, variables) for key, item in value.items()}
        return value
