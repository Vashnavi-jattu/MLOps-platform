"""Command-line application entry point.

Lifecycle commands will be added in later user stories. This initial entry
point confirms that the package can expose the planned ``mlops`` executable.
"""

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from mlops_platform.config import load_config
from mlops_platform.dataset import validate_iranian_churn_csv
from mlops_platform.errors import MLOPsError
from mlops_platform.logging_config import configure_logging, operation_context

logger = logging.getLogger(__name__)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the MLOPs command-line application."""
    # argparse handles help and version output for the CLI.
    parser = argparse.ArgumentParser(
        prog="mlops",
        description="Manage machine-learning projects with the MLOPs platform.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    # Subcommands group related actions; more groups can be added as stories land.
    commands = parser.add_subparsers(dest="command")
    config_parser = commands.add_parser(
        "config", help="Validate project configuration."
    )
    config_commands = config_parser.add_subparsers(dest="config_command", required=True)
    validate_parser = config_commands.add_parser(
        "validate", help="Validate an mlops.yaml file."
    )
    validate_parser.add_argument(
        "path", nargs="?", type=Path, default=Path("mlops.yaml")
    )
    data_parser = commands.add_parser(
        "data", help="Check a training dataset against its schema."
    )
    data_commands = data_parser.add_subparsers(dest="data_command", required=True)
    data_validate_parser = data_commands.add_parser(
        "validate", help="Validate the dataset referenced by an mlops.yaml file."
    )
    data_validate_parser.add_argument(
        "path", nargs="?", type=Path, default=Path("mlops.yaml")
    )
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "config" and args.config_command == "validate":
        # One ID connects the CLI message with every log record from this operation.
        configure_logging()
        with operation_context() as operation_id:
            try:
                config = load_config(args.path)
            except MLOPsError as exc:
                # Known errors have safe details that help the user correct the input.
                logger.warning("CLI operation failed", extra={"error_code": exc.code})
                parser.exit(2, f"error: {exc} (operation ID: {operation_id})\n")
            except Exception:
                # Unknown failures may contain secrets, so show details only in
                # the code and log type.
                # The formatter records the exception type without its sensitive text.
                logger.exception("Unexpected CLI failure")
                parser.exit(
                    1,
                    f"Unexpected error. Check logs with operation ID {operation_id}.\n",
                )
            logger.info(
                "Configuration validated",
                extra={"project_name": config.project.name},
            )
            # Keep normal command results on stdout; structured logs use stderr.
            print(f"Configuration is valid: {args.path}")
            print(f"Project: {config.project.name}")
    elif args.command == "data" and args.data_command == "validate":
        # The config supplies both the dataset location and its target column;
        # loading it also resolves relative paths from the config's directory.
        configure_logging()
        with operation_context() as operation_id:
            try:
                config = load_config(args.path)
                result = validate_iranian_churn_csv(
                    config.dataset.path,
                    target_column=config.dataset.target,
                )
            except MLOPsError as exc:
                logger.warning("CLI operation failed", extra={"error_code": exc.code})
                parser.exit(2, f"error: {exc} (operation ID: {operation_id})\n")
            except Exception:
                logger.exception("Unexpected CLI failure")
                parser.exit(
                    1,
                    f"Unexpected error. Check logs with operation ID {operation_id}.\n",
                )
            logger.info(
                "Dataset validated",
                extra={"row_count": result.row_count, "target": result.target_column},
            )
            print(f"Dataset is valid: {result.path}")
            print(f"Rows: {result.row_count}; columns: {result.column_count}")
            print(f"Target: {result.target_column}")
    return 0


if __name__ == "__main__":
    # Convert main's return code into the process exit status.
    raise SystemExit(main())
