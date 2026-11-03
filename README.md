# MLOPs

MLOPs is a self-service platform for managing a machine-learning model through training, experiment tracking, evaluation, versioning, deployment, and monitoring. The goal is to build a working, production-style project that demonstrates software engineering, machine-learning engineering, MLOps, and cloud infrastructure.

The platform is planned to include a Python CLI, a FastAPI control API, and a Next.js dashboard. The first releases focus on a reliable local Python workflow; Kubernetes, advanced release strategies, and Azure deployment come later.

## Project status

This repository is at the planning and foundation stage. The product specification is drafted in [`docs/product-specification.md`](docs/product-specification.md). The Python package scaffold (MF-004), local quality checks (MF-005), and typed YAML configuration (MF-006) are in place and verified. MF-007–MF-008 remain planned. The implementation backlog contains 80 user stories, MF-001 through MF-080. A feature is considered implemented only after it works and has been verified; roadmap entries are not claims of existing functionality.

## Development plan

Work through one user story at a time, in dependency order. The current target is **Backlog Phase 1: Software engineering foundation (MF-004–MF-008)**. The planning stories MF-001–MF-003 come first because the foundation work depends on their decisions.

### Phase 1 goal

Establish a maintainable Python package with validated configuration, consistent logging and errors, developer quality checks, and repeatable local setup and CI.

### Phase 1 user stories

| Issue | User story | Acceptance criteria |
| --- | --- | --- |
| MF-004 | As a developer, I want a maintainable repository so code remains organized. | Create `src/mlops_platform`, `tests`, `pyproject.toml`, package entry points, and a successful import check. |
| MF-005 | As a developer, I want automated quality checks so mistakes are caught early. | Ruff, mypy, pytest, and pre-commit run successfully; add sample tests. |
| MF-006 | As a developer, I want typed YAML configuration so projects can be configured safely. | Pydantic validates required fields, defaults, ranges, and invalid input with actionable errors. |
| MF-007 | As a developer, I want structured logs and understandable errors so failures are easy to debug. | Logs include timestamps, levels, and operation IDs; exceptions provide safe, clear details. |
| MF-008 | As a contributor, I want consistent setup commands and CI so the repository is easy to work with. | README setup instructions, Makefile commands, and GitHub Actions Python lint/type/test checks all work. |

### Planned Phase 1 technology

- Python package using a `src/` layout
- `pyproject.toml` for package metadata and development tools
- Pydantic-validated YAML configuration
- Ruff, mypy, pytest, and pre-commit
- Makefile commands and GitHub Actions checks

These are planned choices for this phase; they are not all implemented yet.

### Validate project configuration

Start from [`examples/mlops.yaml`](examples/mlops.yaml), then run:

```bash
mlops config validate examples/mlops.yaml
```

The dataset path is resolved relative to the configuration file. This command validates the configuration structure; it does not inspect or train on the dataset contents.

### Set up Python development checks

Create and activate a virtual environment, then install the project and its development tools:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pre-commit install
```

Run the checks directly:

```bash
ruff check .
ruff format --check .
mypy src
pytest
pre-commit run --all-files
```

## Longer-term direction

After the foundation, the backlog moves on to a reproducible scikit-learn training pipeline, experiment tracking with MLflow, model registration, inference serving, a FastAPI backend, and a web dashboard. Later releases add container orchestration, monitoring, canary releases, rollback, and Azure infrastructure. See [`docs/product-specification.md`](docs/product-specification.md) for product scope and release boundaries, [`docs/architecture.md`](docs/architecture.md) for the system design, [`docs/api-contract.md`](docs/api-contract.md) for planned interfaces, and [`docs/design-decisions.md`](docs/design-decisions.md) for recorded decisions.

## Working agreement

For each story, inspect the existing code and its acceptance criteria, implement only that story, add and run the relevant checks, update documentation, and report what was actually verified. Keep completed, in-progress, planned, and optional work distinct. Do not add credentials to the repository or claim unmeasured performance results.
