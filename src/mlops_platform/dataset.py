"""Dataset schemas and CSV validation for the initial MLOPs workflow."""

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from mlops_platform.errors import DatasetValidationError


@dataclass(frozen=True)
class ColumnRule:
    """Describe the accepted values for one input or target column."""

    name: str
    kind: Literal["integer", "number"]
    minimum: float | None = None
    maximum: float | None = None
    allowed_values: frozenset[str] | None = None


# This schema follows the field names documented in docs/dataset.md. Keep the
# target among the required columns so a file cannot accidentally be used for
# supervised training without its answer column.
IRANIAN_CHURN_SCHEMA: tuple[ColumnRule, ...] = (
    ColumnRule("Call Failure", "integer", minimum=0),
    ColumnRule("Complains", "integer", allowed_values=frozenset({"0", "1"})),
    ColumnRule("Subscription Length", "integer", minimum=0),
    ColumnRule("Charge Amount", "integer", minimum=0, maximum=9),
    ColumnRule("Seconds of Use", "integer", minimum=0),
    ColumnRule("Frequency of use", "integer", minimum=0),
    ColumnRule("Frequency of SMS", "integer", minimum=0),
    ColumnRule("Distinct Called Numbers", "integer", minimum=0),
    ColumnRule("Age Group", "integer", minimum=1, maximum=5),
    ColumnRule("Tariff Plan", "integer", allowed_values=frozenset({"1", "2"})),
    ColumnRule("Status", "integer", allowed_values=frozenset({"1", "2"})),
    # The source labels Age as an integer but does not give a coding range.
    ColumnRule("Age", "integer", minimum=0),
    # The source calls this a value measure but gives no numeric range.
    ColumnRule("Customer Value", "number"),
    ColumnRule("Churn", "integer", allowed_values=frozenset({"0", "1"})),
)


@dataclass(frozen=True)
class DatasetValidationResult:
    """Summary returned when a CSV passes all schema checks."""

    path: Path
    row_count: int
    column_count: int
    target_column: str


def validate_iranian_churn_csv(
    path: str | Path,
    *,
    target_column: str = "Churn",
    schema: tuple[ColumnRule, ...] = IRANIAN_CHURN_SCHEMA,
) -> DatasetValidationResult:
    """Check a CSV's columns, values, and target against the churn schema.

    Extra columns are allowed so users can carry metadata, but all fields in
    the selected schema must exist. Errors identify row and column without
    echoing the potentially sensitive cell value.
    """
    dataset_path = Path(path).expanduser().resolve()
    if not dataset_path.is_file():
        raise DatasetValidationError(f"Dataset file does not exist: '{dataset_path}'.")

    rules = tuple(
        ColumnRule(
            name=target_column if rule.name == "Churn" else rule.name,
            kind=rule.kind,
            minimum=rule.minimum,
            maximum=rule.maximum,
            allowed_values=rule.allowed_values,
        )
        for rule in schema
    )
    expected_names = {rule.name for rule in rules}
    issues: list[str] = []
    row_count = 0

    try:
        with dataset_path.open(encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            headers = reader.fieldnames
            if not headers:
                raise DatasetValidationError(
                    "Dataset CSV is empty or has no header row."
                )

            duplicate_headers = sorted(
                {name for name in headers if headers.count(name) > 1}
            )
            if duplicate_headers:
                names = ", ".join(duplicate_headers)
                raise DatasetValidationError(
                    f"Dataset has duplicate column names: {names}."
                )

            missing_columns = sorted(expected_names - set(headers))
            if missing_columns:
                names = ", ".join(missing_columns)
                raise DatasetValidationError(
                    f"Dataset is missing required columns: {names}."
                )

            for row_number, row in enumerate(reader, start=2):
                row_count += 1
                # DictReader uses a None key when a row has more values than
                # the header; missing trailing values appear as None cells.
                if None in row:
                    issues.append(f"row {row_number}: has more cells than the header")
                for rule in rules:
                    raw_value = row.get(rule.name)
                    if not isinstance(raw_value, str) or not raw_value.strip():
                        issues.append(
                            f"row {row_number}, column '{rule.name}': value is missing"
                        )
                        continue
                    issue = _check_value(raw_value.strip(), rule)
                    if issue:
                        issues.append(
                            f"row {row_number}, column '{rule.name}': {issue}"
                        )
                if len(issues) >= 20:
                    break
    except UnicodeError as exc:
        raise DatasetValidationError(
            "Dataset must be a UTF-8 encoded CSV file."
        ) from exc
    except csv.Error as exc:
        raise DatasetValidationError("Dataset is not a valid CSV file.") from exc
    except OSError as exc:
        raise DatasetValidationError(
            f"Cannot read dataset file '{dataset_path}'."
        ) from exc

    if row_count == 0:
        raise DatasetValidationError("Dataset must contain at least one data row.")
    if issues:
        details = "; ".join(issues[:20])
        extra = " (showing the first 20 issues)" if len(issues) >= 20 else ""
        raise DatasetValidationError(f"Dataset validation failed{extra}: {details}.")

    return DatasetValidationResult(
        path=dataset_path,
        row_count=row_count,
        column_count=len(headers),
        target_column=target_column,
    )


def _check_value(value: str, rule: ColumnRule) -> str | None:
    """Return a short reason when a cell does not satisfy its column rule."""
    if rule.allowed_values is not None and value not in rule.allowed_values:
        allowed = ", ".join(sorted(rule.allowed_values))
        return f"must be one of: {allowed}"

    numeric_value: int | float
    try:
        if rule.kind == "integer":
            # int() rejects decimal strings such as "3.5" instead of rounding.
            numeric_value = int(value)
        else:
            numeric_value = float(value)
            if not math.isfinite(numeric_value):
                return "must be a finite number"
    except ValueError:
        expected = "an integer" if rule.kind == "integer" else "a number"
        return f"must be {expected}"

    if rule.minimum is not None and numeric_value < rule.minimum:
        return f"must be at least {rule.minimum:g}"
    if rule.maximum is not None and numeric_value > rule.maximum:
        return f"must be at most {rule.maximum:g}"
    return None
