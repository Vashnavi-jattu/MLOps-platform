# MLOPs Design Decisions

This document records decisions that affect implementation. Revisit a decision when new requirements or evidence warrant it; record the reason and impact rather than silently changing the contract.

## D-001: Product name

- **Status:** Accepted
- **Decision:** Use **MLOPs** as the product name. Use `mlops-platform` for the Python distribution, `mlops_platform` for the import package, and `mlops` for the command-line executable.
- **Context:** The project owner requested the name MLOPs instead of ModelForge before implementation began.
- **Consequences:** Documentation and new interfaces use MLOPs consistently. Backlog IDs such as MF-001 remain unchanged as identifiers. Before MF-004, align package naming and repository references with this decision.

## D-002: Shared core behind multiple interfaces

- **Status:** Accepted
- **Decision:** Keep lifecycle rules in a shared Python core package. The CLI and later FastAPI control API call the same core services.
- **Context:** Prevents the CLI and web product from implementing different training, registration, and deployment behavior.
- **Consequences:** Command handlers and HTTP route handlers should remain thin adapters. Do not make core services depend on a CLI framework or HTTP request objects.

## D-003: Local MVP before distributed infrastructure

- **Status:** Accepted
- **Decision:** Deliver a single-user local workflow before Kubernetes, Azure hosting, autoscaling, canary releases, or drift alerting.
- **Context:** A verified local train-to-predict lifecycle is the foundation for meaningful deployment and operations work.
- **Consequences:** Docker Compose may provide local dependencies; Redis/RQ and Kubernetes are deferred until a demonstrated requirement needs them.

## D-004: MLflow owns experiment and model tracking

- **Status:** Accepted
- **Decision:** Use MLflow Tracking and Model Registry for runs, metrics, artifacts, and registered model versions.
- **Context:** Avoid building a parallel experiment tracker or model registry.
- **Consequences:** PostgreSQL is the metadata store and object storage holds artifacts. MLOPs-owned API entities, if added later, must have distinct schema ownership and migrations.

## D-005: Persist the complete inference pipeline

- **Status:** Accepted
- **Decision:** Serialize preprocessing together with the fitted estimator and load that same pipeline for inference.
- **Context:** Separate or refitted preprocessing can make training and serving behavior diverge.
- **Consequences:** Evaluation fits transformations only on training partitions; inference applies saved transformations without fitting.

## D-006: API contracts are versioned and explicit

- **Status:** Accepted
- **Decision:** The future control API uses JSON, Pydantic schemas, OpenAPI, and a `/api/v1` prefix.
- **Context:** The frontend needs stable, typed contracts and should not access service databases directly.
- **Consequences:** Breaking changes require a deliberate versioning decision; TypeScript types should be generated from or checked against OpenAPI.

## Open decisions

- Whether training and deployment API operations need durable asynchronous jobs, and when to introduce Redis/RQ.
- Authentication and authorization design before any non-local or multi-user exposure.
- Exact model hyperparameter schema and support for model-specific options.
- Dataset fingerprint algorithm and which source revision/environment metadata to capture.
- Concrete Kubernetes deployment mechanism and Azure identity/secret management approach.
