"""Smoke tests for the initial Python package scaffold."""

import contextlib
import io
import unittest

import mlops_platform
from mlops_platform.cli import main


class PackageImportTests(unittest.TestCase):
    def test_package_imports_with_version(self) -> None:
        # Importing the package should expose its initial version constant.
        self.assertEqual(mlops_platform.__version__, "0.1.0")

    def test_cli_entry_point_shows_help_without_commands(self) -> None:
        # Capture output so this test can check help without cluttering the console.
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main([])

        self.assertEqual(result, 0)
        self.assertIn("usage: mlops", output.getvalue())


if __name__ == "__main__":
    unittest.main()
