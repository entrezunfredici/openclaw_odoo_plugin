from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlparse

from .errors import NotFoundError, ServiceError

try:
    import odoolib
except ImportError as exc:
    odoolib = None
    _ODOOLIB_IMPORT_ERROR = exc
else:
    _ODOOLIB_IMPORT_ERROR = None

class OdooClient:
    """Small Odoo JSON-RPC wrapper with normalized errors."""

    def __init__(self, url: str, port: int, database: str, login: str, password: str) -> None:
        if odoolib is None:
            raise ServiceError(
                "odoolib is not installed. Add 'odoo-client-lib' to the environment."
            ) from _ODOOLIB_IMPORT_ERROR

        hostname = self._normalize_hostname(url)
        try:
            self.client = odoolib.get_connection(
                hostname=hostname,
                protocol="jsonrpcs",
                port=port,
                database=database,
                login=login,
                password=password,
            )
        except Exception as exc:
            raise ServiceError(
                f"Unable to connect to Odoo host '{hostname}' on database '{database}'"
            ) from exc

    @staticmethod
    def _normalize_hostname(url: str) -> str:
        parsed = urlparse(url)
        return parsed.hostname or parsed.path or url

    def get_model_list(self) -> list[dict[str, Any]]:
        try:
            ir_model = self.get_model("ir.model")
            return ir_model.search_read([], ["model", "name", "state"])
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError("Unable to list Odoo models") from exc

    def get_model(self, model_name: str) -> Any:
        try:
            return self.client.get_model(model_name)
        except Exception as exc:
            raise ServiceError(f"Unable to access model '{model_name}'") from exc

    def get(
        self,
        model_name: str,
        domain: Sequence[Any],
        fields: Sequence[str],
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        try:
            model = self.get_model(model_name)
            search_kwargs = {}
            if limit is not None:
                search_kwargs["limit"] = limit
            objects = model.search_read(list(domain), list(fields), **search_kwargs)
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(
                f"Unable to get records matching '{domain}' in '{model_name}'"
            ) from exc

        if not objects:
            raise NotFoundError(
                f"Records matching '{domain}' not found in '{model_name}'"
            )

        return objects

    def post(self, model_name: str, values: Mapping[str, Any]) -> int:
        try:
            model = self.get_model(model_name)
            return model.create(dict(values))
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(f"Unable to create record in '{model_name}'") from exc

    def put(
        self,
        model_name: str,
        object_ids: Sequence[int],
        values: Mapping[str, Any],
    ) -> bool:
        try:
            model = self.get_model(model_name)
            return bool(model.write(list(object_ids), dict(values)))
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(f"Unable to update records in '{model_name}'") from exc

    def delete(self, model_name: str, object_ids: Sequence[int]) -> bool:
        try:
            model = self.get_model(model_name)
            return bool(model.unlink(list(object_ids)))
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(f"Unable to delete records in '{model_name}'") from exc
