"""Structured logging and operation IDs for the MLOPs application."""

import contextvars
import json
import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import TextIO
from uuid import uuid4

# Context variables keep IDs separate if operations later run concurrently.
_operation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "mlops_operation_id", default=None
)


@contextmanager
def operation_context() -> Iterator[str]:
    """Create an ID that links log entries from one operation together."""
    operation_id = str(uuid4())
    token = _operation_id.set(operation_id)
    try:
        yield operation_id
    finally:
        # Restore the previous value so a completed operation cannot affect later logs.
        _operation_id.reset(token)


class _OperationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Mark logs outside a command context instead of leaving the field missing.
        record.operation_id = _operation_id.get() or "unscoped"
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Use UTC so timestamps from different machines can be compared directly.
        timestamp = datetime.fromtimestamp(record.created, UTC)
        entry: dict[str, str] = {
            "timestamp": timestamp.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
            "level": record.levelname,
            "logger": record.name,
            "operation_id": getattr(record, "operation_id", "unscoped"),
            "message": record.getMessage(),
        }
        # Only selected, non-sensitive context is added to structured records.
        for field in ("error_code", "project_name"):
            value = getattr(record, field, None)
            if isinstance(value, str):
                entry[field] = value
        if record.exc_info and record.exc_info[0]:
            # The exception class aids debugging without exposing its message/traceback.
            entry["exception_type"] = record.exc_info[0].__name__
        return json.dumps(entry, ensure_ascii=False)


def configure_logging(
    level: int = logging.INFO, stream: TextIO | None = None
) -> logging.Logger:
    """Configure JSON logs on stderr, or on a supplied stream for tests."""
    logger = logging.getLogger("mlops_platform")
    # Clear only this package's handlers to avoid duplicate output after reconfiguration.
    logger.handlers.clear()
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.addFilter(_OperationFilter())
    handler.setFormatter(_JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    # Child module loggers send records here once, avoiding duplicate root logs.
    logger.propagate = False
    return logger
