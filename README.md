# Orchestrate dbt on Airflow

Local-to-prod feature pipeline scaffold for orchestrating dbt models with Airflow 3 via Astronomer Cosmos, then materializing features into Feast through a GitOps-driven promotion flow.

## High-Level Design

This repository implements a portable feature pipeline with the following shape:

```
Git repo
  │
  ├── config/              # environment-specific YAML configs (local/dev/prod)
  ├── dags/                # Airflow + Cosmos DAG definitions
  ├── dbt_project/         # dbt models, tests, seeds, profiles
  ├── feast_repo/          # Feast feature definitions
  ├── scripts/             # config loader, data fetch, export, docs generation
  ├── tests/               # phase-specific unit, integration, promotion tests
  ├── docs/                # generated dbt docs artifacts
  └── docker-compose.yml   # local Airflow 3 stack
```

### Target Architecture

```
Git repo
    │
    ▼
 CI validation
    │
    ▼
 Airflow 3 + Cosmos (Docker Compose)
    │
    ├── dbt build / test (task-per-model rendering)
    │
    ▼
 Feature marts (DuckDB → Parquet export)
    │
    ▼
 Feast apply + materialize
    │
    ▼
 Online feature store (SQLite local / Redis prod)
```

### Design Principles

The design goal is not merely to run dbt inside Airflow. The goal is to make the pipeline **portable**:

- **Same DAG code** across environments
- **Same dbt project** across environments
- **Same Feast definitions** across environments
- **Environment differences** expressed through configuration
- **Promotions validated** by CI
- **Deployment changes** auditable through Git

### Data Flow Detail

```
Raw Parquet (NYC TLC Yellow Taxi)
    │
    ▼
dbt staging models (stg_yellow_trips, stg_taxi_zones)
    │
    ▼
dbt fact model (fct_trips)
    │
    ▼
dbt feature mart (feature_pickup_zone_hourly)
    │
    ▼
Parquet export (dbt → DuckDB → Parquet)
    │
    ▼
Feast offline store (DuckDB query engine reads Parquet)
    │
    ▼
Feast online store (SQLite local / Redis prod)
```

The dbt→Feast bridge uses a **Parquet artifact** as the exchange format. This is intentional: Feast's DuckDB offline store is a query engine (via ibis), not a database pointer. The Parquet file keeps the dbt↔Feast boundary clean, portable, and free from DuckDB single-writer lock contention.

## Motivation

Many dbt + Airflow examples stop at local execution. They show a DAG running on a laptop, but leave the operational layer implicit:

- How are dbt models rendered as retryable Airflow tasks?
- How are environment-specific connections handled?
- How are secrets avoided in code?
- How is a pipeline promoted from local to dev to prod?
- How do we prove that prod and dev differ only by configuration?
- How are feature engineering artifacts connected to Feast materialization?

This project exists to answer those questions with a working repository, not just a diagram.

## Core Principles

| Principle | Description |
|-----------|-------------|
| **Environment-agnostic DAG code** | DAG Python code contains no `if env == "prod"` branches |
| **Configuration-driven environments** | Local, dev, and prod differ by resolved configuration values |
| **Secrets outside the repo** | The repo contains structure and safe defaults. Secrets are injected at runtime |
| **Local-first validation** | The pipeline is testable on a laptop without cloud credentials |
| **Tested feature engineering** | dbt models and Feast definitions are versioned, tested, and inspectable |
| **Observable orchestration** | Cosmos renders dbt models as discrete Airflow tasks with task-level retry and lineage |
| **GitOps promotion** | Promotion is a Git-based change. The strongest proof point is a dev-to-prod diff that touches no `.py` or `.sql` files |

## Module Architecture

| Module | Responsibility |
|--------|---------------|
| `config/` | Environment-specific YAML settings (local/dev/prod) |
| `dags/` | Airflow and Cosmos orchestration (environment-agnostic) |
| `dbt_project/` | Analytics and feature transformations |
| `feast_repo/` | Feature contracts and materialization config |
| `scripts/` | Operational helpers (config loader, data fetch, export, docs) |
| `tests/` | Phase-specific unit, integration, and promotion validation |
| `docs/` | Generated dbt docs artifacts (manifest, catalog, HTML) |

No module silently owns another module's responsibility.

## Configurability

The project distinguishes between **code** and **configuration**.

**Code** (environment-agnostic logic):
- dbt SQL models
- Airflow DAG structure
- Feast feature definitions
- Test logic

**Configuration** (environment-specific values):
- `config/local.yaml`, `config/dev.yaml`, `config/prod.yaml`
- Environment name (`ENV_NAME`)
- Warehouse connection reference
- Feast online store reference
- Schedule and retry policy
- Materialization window
- Concurrency limits

### The Falsifiable Promotion Claim

> Moving from dev to prod changes resolved configuration, not pipeline source code.

This is enforced by the centralized config loader (`scripts/config.py`) and validated by P4 promotion tests.

## Technology Stack

| Component | Local | Production Target |
|-----------|-------|-------------------|
| **Orchestrator** | Airflow 3 (Docker Compose) | Airflow 3 (Kubernetes) |
| **dbt Renderer** | Astronomer Cosmos 1.15+ | Astronomer Cosmos |
| **Warehouse** | DuckDB | Snowflake / BigQuery |
| **Feature Store** | Feast | Feast |
| **Offline Store** | DuckDB (query engine) | Warehouse-native |
| **Online Store** | SQLite | Redis / DynamoDB |
| **Package Manager** | uv | uv |
| **Lineage** | dbt docs + Airflow Assets | + OpenLineage / Marquez |

### Airflow 3 Architecture

Airflow 3 introduced a component split that requires explicit Docker service definitions:

| Component | Airflow 2 | Airflow 3 |
|-----------|-----------|-----------|
| **DAG Parsing** | scheduler (built-in) | dag-processor (separate service) |
| **Task Scheduling** | scheduler | scheduler |
| **UI / API** | webserver | api-server |
| **Auth** | FAB (admin/admin) | SimpleAuthManager (JSON file) |
| **Task Execution API** | N/A | Execution API (requires `EXECUTION_API_SERVER_URL`) |

### DuckDB Concurrency Constraint

DuckDB enforces a single-writer file lock. The DAG sets `max_active_tasks=1` to serialize dbt task execution. In production (Snowflake/BigQuery), this limit is removed via configuration - the code never changes.

## Phase Plan

| Phase | Status | Description |
|-------|--------|-------------|
| **P0** | ✅ Complete | Repo scaffold (uv, .gitignore, README, directories) |
| **P1** | ✅ Complete | Dataset + feature engineering (dbt + DuckDB + tests) |
| **P2** | ✅ Complete | Orchestration (Airflow 3 + Cosmos + Feast via Docker Compose) |
| **P3** | ✅ Complete | Lineage (dbt docs + Airflow Assets + lineage tests) |
| **P4** | ✅ Complete | Environment config (Pydantic loader + config-only promotion) |
| **P5** | 🔲 Planned | CI/CD and GitOps promotion |

### P5 Deliverables (Planned)

- CI validation pipeline (GitHub Actions)
- DAG import test
- Cosmos render test
- dbt build test
- Feast registry test
- Config-only promotion diff proof

## Local Setup

### Prerequisites

- Git
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker Desktop (for Airflow 3 stack)
- Python 3.11+ (available through uv)

### Install & Sync

```bash
uv sync
```

### Quick Start

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Fetch the dataset
make data

# 3. Build the dbt project
make dbt-build

# 4. Initialize Airflow (database + admin user)
make airflow-init

# 5. Start the Airflow stack
make airflow-up

# 6. Open Airflow UI: http://localhost:8080 (admin/admin)
docker compose logs airflow-webserver # get admin password

# 7. Trigger the feature_platform_pipeline DAG
```

### Running Tests

```bash
make test        # Run all tests
make test-p1     # P1: dbt + DuckDB feature engineering
make test-p2     # P2: Docker Compose + DAG structure
make test-p3     # P3: Lineage + manifest assertions
make test-p4     # P4: Config loader + promotion
```

### Key Makefile Targets

| Target | Description |
|--------|-------------|
| `make data` | Fetch NYC TLC dataset |
| `make dbt-build` | Run dbt build |
| `make dbt-clean` | Clean dbt artifacts |
| `make docs` | Generate dbt docs |
| `make view-docs` | Serve dbt docs locally |
| `make airflow-init` | Initialize Airflow DB + admin user |
| `make airflow-up` | Start Airflow stack |
| `make airflow-down` | Stop Airflow stack |
| `make airflow-logs` | Tail Airflow logs |
| `make test` | Run all tests |
| `make reset-all` | Full reset (clean + rebuild + reinit) |

## Dataset

**Source:** NYC TLC Yellow Taxi Trip Records

**Why this dataset:**
- Public and open
- Realistic timestamp-based feature engineering
- Natural entities (pickup zone, time bucket)
- Easy to sample locally with DuckDB / Parquet
- Supports meaningful features (trip count, duration, fare averages, hourly demand)

**Feature entity:** `pickup_zone_id`
**Feature grain:** pickup zone + hour bucket

**Example features:**
- `trip_count_1h`
- `avg_trip_duration_seconds_1h`
- `p95_trip_duration_seconds_1h`
- `avg_total_amount_1h`
- `avg_trip_distance_miles_1h`

## Key Architectural Decisions

### Why Parquet as the dbt→Feast Bridge?

Feast's DuckDB offline store is a **query engine** (via ibis), not a database pointer. It reads file sources (Parquet/Delta) using DuckDB as the execution engine. A Parquet artifact keeps the dbt↔Feast boundary clean, portable, and free from DuckDB single-writer lock contention.

### Why Docker Compose for Airflow?

Airflow 3 on Windows has POSIX compatibility issues (fork-based process management, path handling). Docker Compose provides a consistent Linux environment for the orchestrator while keeping dbt and Feast development native to the host.

### Why Config-Only Promotion?

The config loader (`scripts/config.py`) reads `config/{ENV_NAME}.yaml` and validates it with Pydantic. Environment differences (warehouse type, schema, concurrency, materialization window) are expressed as configuration, not code branches. This makes promotion a one-line change (`ENV_NAME=dev` → `ENV_NAME=prod`) with zero code modifications.

### Why max_active_tasks=1?

DuckDB enforces a single-writer file lock at the OS level. Parallel dbt tasks would collide on the `.duckdb` file. Setting `max_active_tasks=1` serializes execution. In production (Snowflake/BigQuery), this is removed via config - the DAG code never changes.