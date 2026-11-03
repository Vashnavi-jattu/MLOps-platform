"""Tests for loading and validating MLOPs project configuration."""

import pytest

from mlops_platform.cli import main
from mlops_platform.config import ConfigurationError, load_config

# Keep this sample minimal so tests can check which defaults MLOPs fills in.
VALID_CONFIG = """\
schema_version: 1
project:
  name: churn-demo
dataset:
  path: data/churn.csv
  target: churn
training:
  task: classification
"""


def test_load_config_applies_defaults_and_resolves_dataset_path(tmp_path):
    config_file = tmp_path / "mlops.yaml"
    config_file.write_text(VALID_CONFIG, encoding="utf-8")

    config = load_config(config_file)

    assert config.training.test_size == 0.2
    assert config.training.random_seed == 42
    assert config.tracking.experiment_name == "churn-demo"
    assert config.registry.model_name == "churn-demo"
    assert config.dataset.path == (tmp_path / "data/churn.csv").resolve()


def test_load_config_rejects_out_of_range_test_size(tmp_path):
    config_file = tmp_path / "mlops.yaml"
    config_file.write_text(VALID_CONFIG + "  test_size: 1.2\n", encoding="utf-8")

    # The message should identify the exact setting that needs correction.
    with pytest.raises(ConfigurationError, match="training.test_size"):
        load_config(config_file)


def test_load_config_rejects_unknown_fields(tmp_path):
    config_file = tmp_path / "mlops.yaml"
    config_file.write_text(VALID_CONFIG + "unknown_setting: true\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Extra inputs are not permitted"):
        load_config(config_file)


def test_load_config_reports_invalid_yaml(tmp_path):
    config_file = tmp_path / "mlops.yaml"
    config_file.write_text("project: [broken\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Invalid YAML.*line"):
        load_config(config_file)


def test_cli_validates_a_config_file(tmp_path, capsys):
    config_file = tmp_path / "mlops.yaml"
    config_file.write_text(VALID_CONFIG, encoding="utf-8")

    assert main(["config", "validate", str(config_file)]) == 0
    assert "Configuration is valid" in capsys.readouterr().out


def test_cli_returns_error_for_invalid_config(tmp_path, capsys):
    config_file = tmp_path / "mlops.yaml"
    config_file.write_text(VALID_CONFIG + "  test_size: 1.2\n", encoding="utf-8")

    # A bad config should make the command fail and write a useful error to stderr.
    with pytest.raises(SystemExit) as exit_error:
        main(["config", "validate", str(config_file)])

    assert exit_error.value.code == 2
    assert "training.test_size" in capsys.readouterr().err
