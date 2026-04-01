from .errors import NotFoundError, ServiceError

try:
    import keyring
except ImportError as exc:
    keyring = None
    _KEYRING_IMPORT_ERROR = exc
else:
    _KEYRING_IMPORT_ERROR = None

class SecretService:
    """Store secret data in the local keyring service."""

    def __init__(self, service_name: str) -> None:
        if keyring is None:
            raise ServiceError(
                "keyring is not installed. Add 'keyring' to the environment."
            ) from _KEYRING_IMPORT_ERROR

        self.service_name = service_name

    def save_secret(self, name: str, secret: str) -> None:
        try:
            keyring.set_password(self.service_name, name, secret)
        except Exception as exc:
            raise ServiceError(
                f"Unable to save secret '{name}' for service '{self.service_name}'"
            ) from exc

    def get_secret(self, name: str) -> str:
        try:
            secret = keyring.get_password(self.service_name, name)
        except Exception as exc:
            raise ServiceError(
                f"Unable to read secret '{name}' for service '{self.service_name}'"
            ) from exc

        if secret is None:
            raise NotFoundError(
                f"Secret '{name}' not found for service '{self.service_name}'"
            )

        return secret
