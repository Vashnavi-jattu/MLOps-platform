# MLOPs Interface and Data Contracts

## Status

This is the initial contract draft for MF-003, based on the [product specification](product-specification.md) and [architecture](architecture.md). These interfaces are planned; they are not implemented endpoints or guarantees of current behavior. Refine them with a design decision before changing a contract after implementation begins.

## Naming

- Product name: **MLOPs**.
- Python distribution: `mlops-platform`.
- Python import package: `mlops_platform`.
- CLI executable: `mlops`.
- REST API prefix when introduced: `/api/v1`.

## CLI contract

The CLI is the first user-facing interface. Commands should call shared core services. Human-readable output is the default; `--output json` provides machine-readable output where practical. Commands return exit code `0` on success and nonzero on failure, with a concise actionable error on stderr.

| Command | Purpose | Main arguments/options | Successful result |
| --- | --- | --- | --- |
| `mlops init [PATH]` | Create a starter project configuration. | `--name`, `--force` | Writes `mlops.yaml`; refuses to overwrite unless `--force` is provided. |
| `mlops config validate [PATH]` | Validate YAML against the configuration schema. | Config path; defaults to `mlops.yaml` in the current directory. | Reports valid configuration or field-specific validation errors. |
| `mlops train` | Validate data, train configured candidates, evaluate, and log a run. | `--config PATH`, `--seed INT` (optional override) | Returns run ID, status, metrics, and artifact location. |
| `mlops runs list` | List tracked runs for the configured project/experiment. | `--config PATH`, `--limit INT`, `--output` | Returns run IDs, status, start time, model name, and key metrics. |
| `mlops runs show RUN_ID` | Inspect a tracked run. | Run ID, `--config PATH` | Returns parameters, metrics, lineage, and artifact references. |
| `mlops models list` | List registered model names and versions. | `--config PATH` | Returns model/version, source run, and available stage/alias metadata. |
| `mlops models register RUN_ID` | Register a model artifact from a successful run. | Run ID, `--name NAME`, `--config PATH` | Returns registered model name and version. |
| `mlops models show NAME [VERSION]` | Inspect a registered model/version. | Model name and optional version | Returns version metadata, source run, metrics, and artifact reference. |
| `mlops deploy NAME VERSION` | Start an inference service for a registered version. | Model name, version, `--port`, `--config PATH` | Returns deployment ID, endpoint, and initial status. |
| `mlops deployments status [DEPLOYMENT_ID]` | Inspect one or all local deployments. | Optional deployment ID | Returns status, model version, endpoint, and health state. |
| `mlops predict DEPLOYMENT_ID` | Submit one prediction request. | `--input JSON` or `--input-file PATH` | Returns prediction output and request/deployment metadata. |

The exact option spellings may be adjusted during MF-004/MF-003 implementation, but command responsibilities and shared-core behavior should remain stable.

## Project configuration contract

The YAML file is named `mlops.yaml`. Pydantic validates it at load time, rejects unknown keys, and reports the field path and allowed constraint in validation errors. Paths are resolved relative to the configuration file unless documented otherwise. Secrets are not stored in this file.

```yaml
schema_version: 1

project:
  name: customer-churn
  description: Example binary classification project

dataset:
  path: data/churn.csv
  target: churn

training:
  task: classification
  test_size: 0.2
  random_seed: 42
  models:
    - logistic_regression
    - random_forest

tracking:
  experiment_name: customer-churn
  tracking_uri: http://localhost:5000

registry:
  model_name: customer-churn-classifier
```

### Configuration fields

| Field | Type | Required/default | Validation intent |
| --- | --- | --- | --- |
| `schema_version` | integer | Required; initially `1` | Reject unsupported versions with an upgrade message. |
| `project.name` | string | Required | Non-empty; stable identifier using letters, numbers, `_`, or `-`. |
| `project.description` | string | Optional | Human-readable description. |
| `dataset.path` | path string | Required | Must resolve to a readable supported tabular dataset at training time. |
| `dataset.target` | string | Required | Must name a column present in the loaded dataset. |
| `training.task` | enum | Required; initially `classification` | Only supported tasks are accepted. MVP supports binary classification. |
| `training.test_size` | float | Default `0.2` | Strictly greater than `0` and less than `1`; split must leave sufficient examples in each partition. |
| `training.random_seed` | integer | Default `42` | Passed to stochastic splitting/models for reproducibility. |
| `training.models` | list of model identifiers | Default baseline pair | Non-empty; identifiers must be supported by the installed version. |
| `tracking.experiment_name` | string | Defaults to `project.name` | Non-empty MLflow experiment name. |
| `tracking.tracking_uri` | URI string | Defaults to local MLflow configuration | Valid local or configured tracking URI; credentials are supplied separately. |
| `registry.model_name` | string | Defaults to `project.name` | Non-empty registered model name. |

Exact model hyperparameter schemas, categorical/numeric column overrides, and remote credential configuration are deferred until a supported use case requires them.

## Core domain structures

The core uses typed Python models for these concepts. They are transport-independent and can be mapped to CLI output and API schemas.

| Structure | Required fields | Notes |
| --- | --- | --- |
| `ProjectConfig` | `schema_version`, `project`, `dataset`, `training`, `tracking`, `registry` | Validated representation of `mlops.yaml`. |
| `TrainingRun` | `run_id`, `project_name`, `status`, `started_at`, `config_fingerprint` | Also references metrics, parameters, source revision, dataset fingerprint, and artifact URIs when available. |
| `EvaluationMetrics` | `precision`, `recall`, `f1`, `roc_auc`, `confusion_matrix` | Calculated on held-out data; undefined metrics must be represented explicitly, not fabricated. |
| `ModelVersion` | `name`, `version`, `source_run_id`, `artifact_uri`, `created_at` | Registry-backed immutable version reference; promotion aliases/stages are optional later metadata. |
| `Deployment` | `deployment_id`, `model_name`, `model_version`, `status`, `endpoint`, `created_at` | Status is one of `pending`, `starting`, `healthy`, `failed`, or `stopped`. |
| `PredictionRequest` | `deployment_id`, `instances` | `instances` is a non-empty list of feature records; allowed feature names/types are validated against the model contract. |
| `PredictionResponse` | `predictions`, `model_name`, `model_version`, `request_id` | Includes probabilities only when supported by the selected estimator. |

Timestamps are UTC ISO 8601 values at API boundaries. Run/deployment IDs are opaque strings. Artifact locations are references, not credentials or embedded binary content.

## Planned REST API contract (v0.2)

The control API is a transport adapter over the shared core. It uses JSON, Pydantic request/response schemas, and OpenAPI. Initial routes are:

| Method and path | Purpose | Expected response |
| --- | --- | --- |
| `GET /api/v1/health` | Control API liveness/readiness summary. | `200` health status and service version. |
| `GET /api/v1/projects` | List configured/known projects. | `200` array of project summaries. |
| `POST /api/v1/projects` | Create a project from validated configuration. | `201` project summary; `422` for invalid fields. |
| `GET /api/v1/projects/{project_id}` | Read project details. | `200` project; `404` if missing. |
| `POST /api/v1/projects/{project_id}/runs` | Start a training run. | Initially `201` run result if synchronous; if background execution is introduced, return `202` with a run ID. |
| `GET /api/v1/runs` | List runs, optionally filtered by project. | `200` paginated run summaries. |
| `GET /api/v1/runs/{run_id}` | Read run metrics, parameters, status, and artifacts. | `200` run; `404` if missing. |
| `GET /api/v1/models` | List registered models and versions. | `200` model summaries. |
| `POST /api/v1/models` | Register a successful run as a model version. | `201` model version; `409` for invalid/conflicting state. |
| `GET /api/v1/models/{name}/versions/{version}` | Read model version metadata. | `200` version; `404` if missing. |
| `POST /api/v1/deployments` | Deploy a registered model version. | `201` deployment or `202` if deployment is asynchronous. |
| `GET /api/v1/deployments` | List deployments. | `200` deployment summaries. |
| `GET /api/v1/deployments/{deployment_id}` | Read deployment state and endpoint. | `200` deployment; `404` if missing. |
| `POST /api/v1/deployments/{deployment_id}/predictions` | Submit prediction instances. | `200` prediction response; `422` for invalid feature data. |

Pagination, authentication, and authorization details must be specified before exposing the API outside the trusted local development environment. The frontend must call these routes and must not query MLflow or storage directly.

### Representative request and response shapes

These examples establish field names and relationships; implementation may add optional metadata without changing the meaning of required fields.

Create a project with the validated configuration:

```json
{
  "config": {
    "schema_version": 1,
    "project": { "name": "customer-churn" },
    "dataset": { "path": "data/churn.csv", "target": "churn" },
    "training": { "task": "classification", "test_size": 0.2, "random_seed": 42 },
    "tracking": { "experiment_name": "customer-churn" },
    "registry": { "model_name": "customer-churn-classifier" }
  }
}
```

Start a run and receive its lifecycle status:

```json
// POST /api/v1/projects/customer-churn/runs
{ "models": ["logistic_regression", "random_forest"] }
```

```json
// Synchronous response: 201 Created
{
  "run_id": "opaque-run-id",
  "project_name": "customer-churn",
  "status": "finished",
  "metrics": { "precision": 0.0, "recall": 0.0, "f1": 0.0, "roc_auc": 0.0 },
  "artifact_uris": []
}
```

Register a successful run:

```json
// POST /api/v1/models
{ "run_id": "opaque-run-id", "name": "customer-churn-classifier" }
```

```json
// 201 Created
{
  "name": "customer-churn-classifier",
  "version": "1",
  "source_run_id": "opaque-run-id",
  "artifact_uri": "mlflow-artifact-reference"
}
```

Deploy that immutable version and request predictions:

```json
// POST /api/v1/deployments
{ "model_name": "customer-churn-classifier", "model_version": "1" }
```

```json
// POST /api/v1/deployments/opaque-deployment-id/predictions
{
  "instances": [
    { "tenure": 12, "monthly_charges": 70.0, "contract": "month-to-month" }
  ]
}
```

```json
{
  "predictions": [{ "label": 1, "probability": 0.73 }],
  "model_name": "customer-churn-classifier",
  "model_version": "1",
  "request_id": "opaque-request-id"
}
```

The numeric metric and prediction values above illustrate shape only; they are not benchmark results or expected model performance.

## Error response shape

API errors use a consistent JSON envelope. Validation errors may include multiple field issues.

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request contains invalid fields.",
    "request_id": "opaque-request-id",
    "details": [
      { "field": "dataset.target", "message": "Column was not found." }
    ]
  }
}
```

Never include secrets, credentials, full environment dumps, or sensitive file contents in errors or logs. Use appropriate HTTP statuses: `400` malformed request, `404` unknown resource, `409` invalid lifecycle transition, `422` schema/semantic validation, and `500` unexpected server error with a safe message and request ID.
