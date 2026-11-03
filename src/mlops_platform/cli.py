"""Command-line application entry point.

Lifecycle commands will be added in later user stories. This initial entry
point confirms that the package can expose the planned ``mlops`` executable.
"""

import argparse
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Run the MLOPs command-line application."""
    # argparse provides the standard --help behavior for the future commands.
    parser = argparse.ArgumentParser(
        prog="mlops",
        description="Manage machine-learning projects with the MLOPs platform.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    args = parser.parse_args(argv)

    # Until lifecycle commands are added, a bare invocation displays the help.
    if not vars(args):
        parser.print_help()
    return 0


if __name__ == "__main__":
    # Convert main's return code into the process exit status.
    raise SystemExit(main())
