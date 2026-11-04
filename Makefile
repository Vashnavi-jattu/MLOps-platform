# Use the Python interpreter from the active virtual environment.
PYTHON ?= python

.PHONY: install lint format-check typecheck test check

install:
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check .

format-check:
	$(PYTHON) -m ruff format --check .

typecheck:
	$(PYTHON) -m mypy src

test:
	$(PYTHON) -B -m pytest

# Keep one local command for all quality checks used by CI.
check: lint format-check typecheck test
