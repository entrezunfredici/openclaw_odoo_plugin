"""Public package exports for the embedded Odoo connector."""

from .access_profiles import AccessProfile, AccessProfiles
from .action_executor import ActionExecutor
from .action_log import ActionLogEntry, ActionLogStore
from .connection_profiles import ConnectionProfile, ConnectionProfiles
from .errors import (
    AuthorizationError,
    ConfigurationError,
    ConfirmationRequiredError,
    ConnectorError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from .odoo_client import OdooClient
from .permission_rules import PermissionDecision, PermissionRule, PermissionRuleEngine
from .rollback_metadata import (
    FULLY_REVERSIBLE,
    NOT_REVERSIBLE,
    PARTIALLY_REVERSIBLE,
    ReversibilityInfo,
)
from .rollback_service import (
    RollbackService,
)
from .secret_service import SecretService
from .snapshot_store import Snapshot, SnapshotStore
from .templates import Template, TemplateStore
from .validators import validate_action_payload, validate_config

__all__ = [
    "AccessProfile",
    "AccessProfiles",
    "ActionExecutor",
    "ActionLogEntry",
    "ActionLogStore",
    "AuthorizationError",
    "ConfigurationError",
    "ConfirmationRequiredError",
    "ConnectionProfile",
    "ConnectionProfiles",
    "ConnectorError",
    "FULLY_REVERSIBLE",
    "NOT_REVERSIBLE",
    "NotFoundError",
    "OdooClient",
    "PARTIALLY_REVERSIBLE",
    "PermissionDecision",
    "PermissionRule",
    "PermissionRuleEngine",
    "ReversibilityInfo",
    "RollbackService",
    "SecretService",
    "ServiceError",
    "Snapshot",
    "SnapshotStore",
    "Template",
    "TemplateStore",
    "ValidationError",
    "validate_action_payload",
    "validate_config",
]
