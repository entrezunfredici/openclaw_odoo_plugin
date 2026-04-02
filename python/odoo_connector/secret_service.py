"""Secret resolution service. Secrets are never exposed to tool responses."""

from __future__ import annotations

import os

from .errors import NotFoundError, ServiceError

try:
    import keyring
except ImportError as exc:
    keyring = None
    _KEYRING_IMPORT_ERROR = exc
else:
    _KEYRING_IMPORT_ERROR = None


class SecretService:
    """Resolve credentials by secret reference with environment fallback."""

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name

    def get_secret(self, secret_ref: str) -> str:
        env_name = f"ODOO_SECRET_{secret_ref.upper()}"
        from_env = os.getenv(env_name)
        if from_env:
            return from_env

        if keyring is None:
            raise ServiceError(
                "No secret backend available; install keyring or set ODOO_SECRET_<REF>",
                {"secret_ref": secret_ref},
            ) from _KEYRING_IMPORT_ERROR

        try:
            secret = keyring.get_password(self.service_name, secret_ref)
        except Exception as exc:
            raise ServiceError(
                "Unable to read secret from keyring",
                {"secret_ref": secret_ref, "service": self.service_name},
            ) from exc

        if secret is None:
            raise NotFoundError("Secret reference not found", {"secret_ref": secret_ref})

        return secret
