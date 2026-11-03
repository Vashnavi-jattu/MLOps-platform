"""Command-line application entry point.

Lifecycle commands will be added in later user stories. This initial entry
point confirms that the package can expose the planned ``mlops`` executable.
"""

import argparse
from collections.abc import Sequence
from pathlib import Path

from mlops_platform.config import load_config
from mlops_platform.errors import ConfigurationError


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
    # Keep configuration commands nested so later CLI groups can share this layout.
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
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "config" and args.config_command == "validate":
        try:
            config = load_config(args.path)
        except ConfigurationError as exc:
            # argparse prints the user-facing error and exits with a failure code.
            parser.exit(2, f"error: {exc}\n")
        print(f"Configuration is valid: {args.path}")
        print(f"Project: {config.project.name}")
    return 0


if __name__ == "__main__":
    # Convert main's return code into the process exit status.
    raise SystemExit(main())
