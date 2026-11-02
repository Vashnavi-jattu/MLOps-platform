# ModelForge Product Specification

## Purpose

ModelForge is a self-service MLOps platform for taking a conventional machine-learning model from a reproducible training run to a managed deployment. It brings training, experiment tracking, evaluation, model versioning, serving, and operational visibility into one workflow exposed through a CLI and, in later releases, a web dashboard.

The project demonstrates practical software engineering, machine-learning engineering, MLOps, and cloud infrastructure through a working system. Each advertised capability must be implemented and verifiable; planned capabilities are not presented as complete.

## Intended users

- **ML engineer:** prepares data, trains and evaluates models, compares runs, and selects a model version.
- **Platform operator/developer:** configures the platform, manages model deployments, and investigates service health.
- **Portfolio reviewer:** follows the documented setup and demo to verify the end-to-end workflow and engineering decisions.

The initial release is designed for one trusted local user. Team collaboration and public multi-tenant access are outside the first release.

## Product goals

1. Make model training reproducible and record the inputs, configuration, metrics, and artifacts for each run.
2. Make model selection evidence-based through held-out evaluation and experiment comparison.
3. Provide a clear path from a selected model version to a working prediction service.
4. Keep the CLI, API, and future web app on shared core services so lifecycle behavior is consistent.
5. Build the platform incrementally, with a usable local release before adding Kubernetes or cloud hosting.

## Core user workflow

1. Create or configure an ML project.
2. Validate the dataset and project configuration.
3. Train one or more models with reproducible settings.
4. Review metrics and compare experiment runs.
5. Register a selected model version with its lineage and artifacts.
6. Deploy that version as an inference API.
7. Check service health and submit validated predictions.
8. Review deployment and model health, then update or roll back a release as the platform gains those capabilities.

## MVP scope: v0.1 local platform

The first usable release focuses on a local, single-user workflow for a traditional tabular classification model. Customer churn is the initial example problem; the platform design should avoid hard-wiring the core lifecycle to that dataset.

The MVP includes:

- A maintainable Python package and YAML project configuration validated with Pydantic.
- Dataset schema checks and a leakage-safe scikit-learn preprocessing/training pipeline.
- A baseline classifier and a comparison classifier with held-out evaluation metrics.
- Reproducible run metadata, parameters, metrics, and model artifacts tracked with MLflow.
- Model registration and version retrieval through MLflow Model Registry.
- A Typer CLI for the core local workflow: initialize/configure, train, inspect runs, register/list models, deploy, check status, and predict.
- A containerized inference service with health checks and input validation.
- Local supporting services through Docker Compose where needed, including PostgreSQL and MinIO for persistent MLflow metadata and artifacts.
- Documentation for setup, architecture, configuration, workflow, and known limitations.

The MVP is complete when a user can follow the documented local setup, train and compare models, register a model, serve predictions from the registered model, and retrieve run and model information after a service restart.

## Later release boundaries

### v0.2: integrated full-stack workflow

- FastAPI control plane with documented REST/JSON endpoints.
- PostgreSQL-backed platform records and version-controlled Alembic migrations.
- Next.js dashboard for projects, experiments, model versions, deployments, and predictions, backed by real API data.
- Integration and end-to-end checks for important user workflows.
- Local Kubernetes support can be introduced after the local container workflow is stable.

### v1.0: production-style operations and cloud deployment

- Kubernetes deployment management, health probes, resource limits, and autoscaling.
- Prometheus/Grafana operational metrics and model/data monitoring, including drift signals.
- Model validation gates, champion/challenger or canary release controls, and rollback.
- Terraform-managed Azure infrastructure and Azure Blob Storage for cloud artifacts.
- CI/CD workflows for quality checks, image delivery, and deployment.
- Security and operational controls appropriate to the selected deployment model.

Release boundaries are directional. A capability remains planned until it is implemented, documented, and verified in the target environment.

## Non-goals for the MVP

- Public hosted service, multi-tenant isolation, organization/team management, or billing.
- Supporting arbitrary ML frameworks, arbitrary user-supplied training code, or every model type.
- Distributed training, GPU scheduling, feature stores, or automated retraining.
- Kubernetes, Azure, autoscaling, canary releases, or drift alerting as prerequisites for the local MVP.
- Replacing MLflow, PostgreSQL, or object storage with custom equivalents.

## Product and engineering constraints

- The web frontend must communicate with the backend over documented APIs; it must not connect directly to PostgreSQL, MLflow, or Kubernetes.
- CLI and API behavior should reuse shared core services rather than duplicating lifecycle logic.
- Training and inference must use the same serialized preprocessing/model pipeline.
- Evaluation must use held-out data, and preprocessing must not be fitted on held-out data.
- Configuration and secrets must stay outside source code; credentials must not be committed.
- Use a simple modular architecture and add background jobs or additional services only when a demonstrated workflow needs them.
- Keep implementation status explicit: implemented, in progress, planned, or optional.

## Success criteria

- A new contributor can install and run the local MVP using repository documentation.
- A documented dataset produces reproducible tracked runs with metrics and retrievable artifacts.
- A registered model can be loaded by the inference service and return validated predictions.
- Invalid configuration, malformed input data, and invalid prediction requests produce clear errors.
- Core workflows have automated checks and their results are reported accurately.
- Documentation distinguishes working functionality from planned work and records meaningful limitations.

## Assumptions to revisit

- The initial dataset is a legally usable customer churn dataset with a documented source and license.
- Local development can use Docker Compose for PostgreSQL, MinIO, and MLflow services.
- The first model family is scikit-learn classification; XGBoost is optional and should be added only if it improves a demonstrated use case.
- Azure is the target cloud for the eventual hosted release.
