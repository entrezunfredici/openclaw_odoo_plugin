"""Access profile storage and defaults."""
from __future__ import annotations
from dataclasses import dataclass
from .errors import ConfigurationError, NotFoundError


@dataclass(slots=True)
class AccessProfile:
    id: str
    label: str
    connection_profile_id: str
    enabled: bool
    default_read_confirmation: bool
    default_create_confirmation: bool
    default_write_confirmation: bool
    default_delete_confirmation: bool

    def default_confirmation_for(self, operation: str) -> bool:
        return {
            "read": self.default_read_confirmation,
            "create": self.default_create_confirmation,
            "write": self.default_write_confirmation,
            "delete": self.default_delete_confirmation,
        }.get(operation, True)


class AccessProfiles:
    def __init__(self, profiles: list[AccessProfile]) -> None:
        self._profiles = {profile.id: profile for profile in profiles}

    @classmethod
    def from_config(cls, config: dict) -> "AccessProfiles":
        raw_profiles = config.get("access_profiles", [])
        profiles = [AccessProfile(**item) for item in raw_profiles]

        if not profiles:
            raise ConfigurationError("No access profiles configured")

        return cls(profiles)

    def get(self, profile_id: str) -> AccessProfile:
        profile = self._profiles.get(profile_id)
        if profile is None:
            raise NotFoundError(
                f"Access profile '{profile_id}' not found",
                {"access_profile_id": profile_id},
            )
        if not profile.enabled:
            raise ConfigurationError(
                f"Access profile '{profile_id}' is disabled",
                {"access_profile_id": profile_id},
            )
        return profile
