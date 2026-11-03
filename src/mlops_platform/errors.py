"""Safe application errors shared by the CLI and core services."""


class MLOPsError(Exception):
    """Base class for errors that are safe to show to a user."""

    code = "application_error"


class ConfigurationError(MLOPsError):
    """A readable error raised when project configuration cannot be loaded."""

    code = "invalid_configuration"
