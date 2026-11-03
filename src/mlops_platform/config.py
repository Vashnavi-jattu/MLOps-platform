"""Typed loading and validation for MLOPs YAML project configuration."""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from mlops_platform.errors import ConfigurationError


class _ConfigModel(BaseModel):
    # Reject misspelled keys and trim accidental spaces before checking values.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProjectSettings(_ConfigModel):
    name: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_-]+$")
    description: str | None = None


class DatasetSettings(_ConfigModel):
    path: Path
    target: str = Field(min_length=1)

    @field_validator("path", mode="before")
    @classmethod
    def reject_empty_path(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            raise ValueError("dataset path must not be empty")
        return value


# This allowlist prevents configs from requesting models the MVP cannot run.
ModelName = Literal["logistic_regression", "random_forest"]


def _default_models() -> list[ModelName]:
    return ["logistic_regression", "random_forest"]


class TrainingSettings(_ConfigModel):
    task: Literal["classification"]
    test_size: float = Field(default=0.2, gt=0, lt=1)
    random_seed: int = Field(default=42, ge=0)
    models: list[ModelName] = Field(default_factory=_default_models, min_length=1)


class TrackingSettings(_ConfigModel):
    experiment_name: str = Field(min_length=1)
    tracking_uri: str = Field(default="http://localhost:5000", min_length=1)


class RegistrySettings(_ConfigModel):
    model_name: str = Field(min_length=1)


class ProjectConfig(_ConfigModel):
    schema_version: Literal[1]
    project: ProjectSettings
    dataset: DatasetSettings
    training: TrainingSettings
    tracking: TrackingSettings
    registry: RegistrySettings

    @model_validator(mode="before")
    @classmethod
    def default_names_from_project(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        project = values.get("project")
        if not isinstance(project, dict) or not isinstance(project.get("name"), str):
            return values

        prepared = values.copy()
        project_name = project["name"]
        # Reuse the project name unless the user supplied explicit names.
        for section_name, field_name in (
            ("tracking", "experiment_name"),
            ("registry", "model_name"),
        ):
            section = values.get(section_name, {})
            if isinstance(section, dict):
                section = section.copy()
                section.setdefault(field_name, project_name)
                prepared[section_name] = section
        return prepared


def load_config(path: str | Path = "mlops.yaml") -> ProjectConfig:
    """Load YAML, apply documented defaults, and return validated settings."""
    config_path = Path(path).expanduser().resolve()
    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ConfigurationError(
            f"Cannot read configuration file '{config_path}'."
        ) from exc

    try:
        # safe_load parses ordinary YAML values without constructing Python objects.
        values = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        location = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        raise ConfigurationError(f"Invalid YAML in '{config_path}'{location}.") from exc

    if not isinstance(values, dict):
        raise ConfigurationError(
            f"Configuration file '{config_path}' must contain a YAML mapping."
        )

    values = _resolve_dataset_path(values, config_path.parent)
    try:
        return ProjectConfig.model_validate(values)
    except ValidationError as exc:
        # Report field paths and messages without echoing the config values.
        problems = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors(include_input=False, include_url=False)
        )
        raise ConfigurationError(
            f"Invalid configuration in '{config_path}': {problems}"
        ) from exc


def _resolve_dataset_path(values: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    """Resolve relative dataset paths from the directory containing the YAML file."""
    dataset = values.get("dataset")
    if not isinstance(dataset, dict) or not isinstance(dataset.get("path"), str):
        return values

    dataset_path = Path(dataset["path"]).expanduser()
    if dataset_path.is_absolute():
        return values

    updated = values.copy()
    updated_dataset = dataset.copy()
    # The config file's folder is stable even when the CLI runs elsewhere.
    updated_dataset["path"] = (base_dir / dataset_path).resolve()
    updated["dataset"] = updated_dataset
    return updated
