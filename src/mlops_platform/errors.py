"""Safe application errors shared by the CLI and core services."""


class MLOPsError(Exception):
    """Base class for errors that are safe to show to a user."""

    # Callers can handle error categories without parsing the human-readable message.
    code = "application_error"


class ConfigurationError(MLOPsError):
    """A readable error raised when project configuration cannot be loaded."""

    # This code is included in structured logs for configuration failures.
    code = "invalid_configuration"


class DatasetValidationError(MLOPsError):
    """A readable error raised when a training dataset violates its schema."""

    # A stable code lets the CLI and future API report this error consistently.
    code = "invalid_dataset"
