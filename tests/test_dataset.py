"""Tests for training dataset schema validation."""

import csv

import pytest

from mlops_platform.dataset import IRANIAN_CHURN_SCHEMA, validate_iranian_churn_csv
from mlops_platform.errors import DatasetValidationError

# Derive headers from the real schema so test rows stay aligned if a field is
# added, removed, or reordered in the validator.
HEADERS = [rule.name for rule in IRANIAN_CHURN_SCHEMA]
# One fully valid record is the baseline; negative tests change only one value
# at a time so each failure points to the rule under test.
VALID_ROW = [
    "1",
    "0",
    "12",
    "3",
    "1000",
    "20",
    "5",
    "8",
    "3",
    "1",
    "1",
    "30",
    "25.5",
    "0",
]


def write_dataset(path, headers=HEADERS, row=VALID_ROW):
    """Write a small CSV fixture that tests can modify for invalid cases.

    Passing ``row=None`` writes only the header, which lets tests represent an
    empty dataset without maintaining separate CSV-writing code.
    """
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        if row is not None:
            writer.writerow(row)
    return path


def test_valid_dataset_returns_a_summary(tmp_path):
    """Accept a correctly shaped row and report its basic dimensions."""
    dataset_path = write_dataset(tmp_path / "valid.csv")

    result = validate_iranian_churn_csv(dataset_path)

    assert result.row_count == 1
    assert result.column_count == len(HEADERS)
    assert result.target_column == "Churn"


def test_rejects_missing_required_column(tmp_path):
    """Reject files that cannot provide all inputs and the prediction target."""
    headers = [name for name in HEADERS if name != "Churn"]
    row = VALID_ROW[:-1]
    dataset_path = write_dataset(tmp_path / "missing-target.csv", headers, row)

    with pytest.raises(DatasetValidationError, match="missing required columns: Churn"):
        validate_iranian_churn_csv(dataset_path)


@pytest.mark.parametrize(
    ("column", "replacement", "message"),
    [
        ("Call Failure", "one", "must be an integer"),
        ("Complains", "2", "must be one of: 0, 1"),
        ("Charge Amount", "10", "must be at most 9"),
        ("Subscription Length", "", "value is missing"),
        ("Churn", "2", "must be one of: 0, 1"),
        ("Customer Value", "NaN", "must be a finite number"),
    ],
)
def test_rejects_invalid_values(tmp_path, column, replacement, message):
    """Exercise type, category, range, missing-value, and target checks."""
    row = VALID_ROW.copy()
    row[HEADERS.index(column)] = replacement
    dataset_path = write_dataset(tmp_path / "invalid.csv", row=row)

    with pytest.raises(DatasetValidationError, match=message):
        validate_iranian_churn_csv(dataset_path)


def test_rejects_dataset_with_no_rows(tmp_path):
    """Require at least one example row after the CSV header."""
    dataset_path = write_dataset(tmp_path / "empty.csv", row=None)

    with pytest.raises(DatasetValidationError, match="at least one data row"):
        validate_iranian_churn_csv(dataset_path)


def test_rejects_nonexistent_dataset(tmp_path):
    """Give a clear validation error when the configured file is absent."""
    with pytest.raises(DatasetValidationError, match="does not exist"):
        validate_iranian_churn_csv(tmp_path / "missing.csv")
