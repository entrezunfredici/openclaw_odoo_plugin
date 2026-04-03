from __future__ import annotations

import time
from typing import Any

from .errors import ServiceError


class ModelMetadataService:
    """Fetch and cache Odoo model metadata."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._cache: dict[tuple[str, str], dict[str, Any]] = {}
        self._cache_expiry: dict[tuple[str, str], float] = {}

    def get_fields_metadata(
        self,
        client: Any,
        profile_id: str,
        model_name: str,
    ) -> dict[str, dict[str, Any]]:
        cache_key = (profile_id, model_name)
        now = time.time()

        if cache_key in self._cache and self._cache_expiry.get(cache_key, 0) > now:
            return self._cache[cache_key]

        try:
            model = client.get_model(model_name)
            metadata = model.fields_get(
                attributes=["type", "required", "readonly", "relation", "selection", "string"]
            )
        except Exception as e:
            raise ServiceError(
                f"Unable to fetch fields metadata for model '{model_name}'"
            ) from e

        if not isinstance(metadata, dict):
            raise ServiceError(
                f"Invalid metadata returned for model '{model_name}'"
            )

        self._cache[cache_key] = metadata
        self._cache_expiry[cache_key] = now + self.ttl_seconds
        return metadata

    def invalidate_model(self, profile_id: str, model_name: str) -> None:
        cache_key = (profile_id, model_name)
        self._cache.pop(cache_key, None)
        self._cache_expiry.pop(cache_key, None)

    def clear(self) -> None:
        self._cache.clear()
        self._cache_expiry.clear()
