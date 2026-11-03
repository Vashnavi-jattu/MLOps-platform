"""Tests for structured MLOPs logging."""

import json
from io import StringIO

from mlops_platform.logging_config import configure_logging, operation_context


def test_logs_include_timestamp_level_and_operation_id():
    output = StringIO()
    logger = configure_logging(stream=output)

    # The ID yielded by the context should be the same ID written on each log record.
    with operation_context() as operation_id:
        logger.info("Configuration loaded", extra={"project_name": "churn-demo"})

    entry = json.loads(output.getvalue())
    assert entry["timestamp"].endswith("Z")
    assert entry["level"] == "INFO"
    assert entry["operation_id"] == operation_id
    assert entry["project_name"] == "churn-demo"


def test_exception_logs_type_without_exception_message():
    output = StringIO()
    logger = configure_logging(stream=output)

    # A raised error can contain sensitive details; the formatter must omit them.
    try:
        raise ValueError("password=do-not-log")
    except ValueError:
        logger.exception("Operation failed")

    entry = json.loads(output.getvalue())
    assert entry["exception_type"] == "ValueError"
    assert "do-not-log" not in output.getvalue()
    assert "Operation failed" in output.getvalue()
