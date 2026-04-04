"""Template store — reusable payload templates for bounded actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import NotFoundError, ValidationError


@dataclass
class Template:
    id: str
    label: str
    action: str
    required_variables: list[str]
    payload_template: dict[str, Any]
    enabled: bool

    def render(self, variables: dict[str, Any]) -> dict[str, Any]:
        """Render the template by substituting {variable_name} placeholders."""
        missing = [v for v in self.required_variables if v not in variables]
        if missing:
            raise ValidationError(
                f"Template '{self.id}' is missing required variables",
                {"missing": missing},
            )

        def _substitute(obj: Any) -> Any:
            if isinstance(obj, str):
                for k, v in variables.items():
                    obj = obj.replace(f"{{{k}}}", str(v))
                return obj
            if isinstance(obj, dict):
                return {k: _substitute(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_substitute(i) for i in obj]
            return obj

        return _substitute(self.payload_template)


class TemplateStore:
    def __init__(self, templates: list[Template]) -> None:
        self._templates = {t.id: t for t in templates}

    @classmethod
    def from_config(cls, config: dict) -> "TemplateStore":
        raw = config.get("templates", [])
        return cls([Template(**item) for item in raw])

    def get(self, template_id: str) -> Template:
        template = self._templates.get(template_id)
        if template is None:
            raise NotFoundError(f"Template '{template_id}' not found", {"template_id": template_id})
        if not template.enabled:
            raise NotFoundError(f"Template '{template_id}' is disabled", {"template_id": template_id})
        return template

    def list_templates(self) -> list[Template]:
        return list(self._templates.values())
