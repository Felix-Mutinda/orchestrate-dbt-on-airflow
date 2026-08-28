# dbt-airflow-cosmos-feast

Local-to-prod feature platform scaffold for orchestrating dbt models with Airflow via Astronomer Cosmos, then materializing features into Feast through a GitOps-driven promotion flow.

---

## High-level design

This repository implements a portable feature pipeline with the following shape:

```text
Git repo
  │
  ├── config/          # environment configuration
  ├── dags/            # Airflow + Cosmos DAG definitions
  ├── dbt_project/     # dbt models, tests, seeds, profiles
  ├── feast_repo/      # Feast feature definitions
  ├── scripts/         # dataset fetch, promotion diff, local runners
  ├── tests/           # unit, integration, promotion tests
  └── deploy/          # GitOps overlays / environment deployment config
```

Target architecture:

```text
Git repo
   │
   ▼
CI validation
   │
   ▼
Airflow + Cosmos
   │
   ├── dbt build / test
   │
   ▼
Feature marts
   │
   ▼
Feast apply + materialize
   │
   ▼
Online feature store
```

The design goal is not merely to run dbt inside Airflow. The goal is to make the pipeline portable:

- same DAG code across environments
- same dbt project across environments
- same Feast definitions across environments
- environment differences expressed through configuration
- promotions validated by CI
- deployment changes auditable through Git

---

## Motivation

Many dbt + Airflow examples stop at local execution. They show a DAG running on a laptop, but leave the operational layer implicit:

- How are dbt models rendered as retryable Airflow tasks?
- How are environment-specific connections handled?
- How are secrets avoided in code?
- How is a pipeline promoted from local to dev to prod?
- How do we prove that prod and dev differ only by configuration?
- How are feature engineering artifacts connected to Feast materialization?

This project exists to answer those questions with a working repository, not just a diagram.

---

## Core principles

1. **Environment-agnostic DAG code**  
   DAG Python code should not contain environment branches such as `if env == "prod"`.

2. **Configuration-driven environments**  
   Local, dev, staging, and prod differ by resolved configuration values.

3. **Secrets outside the repo**  
   The repo contains structure and safe defaults. Secrets are injected at runtime or deployment time.

4. **Local-first validation**  
   The pipeline should be testable on a laptop without cloud credentials.

5. **Tested feature engineering**  
   dbt models and Feast definitions are versioned, tested, and inspectable.

6. **Observable orchestration**  
   Cosmos should render dbt models as discrete Airflow tasks, enabling task-level retry and lineage.

7. **GitOps promotion**  
   Promotion is a Git-based change. The strongest proof point is a dev-to-prod diff that touches no `.py` or `.sql` files.

---

## Scalability

This scaffold is designed to scale in several directions.

### Pipeline scalability

- dbt models can be selected and run incrementally.
- Cosmos can render models as independent Airflow tasks.
- Task-level retries isolate failures to individual models.
- Future versions can partition work by business vertical, domain, or tenant.

### Data scalability

- Local execution uses DuckDB and Parquet.
- Production can swap in a more durable warehouse or object-store-backed table format.
- Feature marts remain contractual outputs consumed by Feast.

### Platform scalability

- Environment overlays allow multiple deployment targets.
- CI gates can validate render, build, tests, and promotion rules.
- The same repo structure can support multiple pipelines if the project grows.

---

## Modularity

The system is intentionally split into bounded concerns.

| Module | Responsibility |
|---|---|
| `config/` | Environment-specific settings |
| `dags/` | Airflow and Cosmos orchestration |
| `dbt_project/` | Analytics and feature transformations |
| `feast_repo/` | Feature contracts and materialization config |
| `scripts/` | Operational helpers |
| `tests/` | Unit, integration, and promotion validation |
| `deploy/` | GitOps environment overlays |

No module should silently own another module's responsibility.

---

## Configurability

The project will distinguish between code and configuration.

Examples of code:

- dbt SQL models
- Airflow DAG structure
- Feast feature definitions
- test logic

Examples of configuration:

- environment name
- dbt target
- warehouse connection reference
- Feast online store reference
- schedule
- retry policy
- dataset sample size
- deployment overlay values

The long-term target is a falsifiable promotion property:

> Moving from dev to prod should change resolved configuration, not pipeline source code.

---

## Dataset choice

Planned dataset for feature engineering:

**NYC TLC Yellow Taxi Trip Records**

Why this dataset:

- public and open
- realistic timestamp-based feature engineering
- natural entities such as pickup zone and time bucket
- easy to sample locally with DuckDB / Parquet
- supports meaningful features such as trip count, duration, fare averages, and hourly demand

Feature entity:

```text
pickup_zone_id
```

Feature grain:

```text
pickup zone + hour bucket
```

Example features:

- `trip_count_1h`
- `avg_trip_duration_seconds_1h`
- `p95_trip_duration_seconds_1h`
- `avg_total_amount_1h`
- `avg_trip_distance_miles_1h`


---

## Phase plan

### P0 - Repo scaffold

Deliverables:

- `uv` project
- `.gitignore`
- `README.md`
- placeholder directories

### P1 - Dataset and feature engineering

Deliverables:

- dataset fetch script
- local Parquet sample
- DuckDB-based raw layer
- staging dbt models
- feature mart dbt models
- feature engineering tests

### P2 - Orchestration

Deliverables:

- Airflow local config
- Cosmos DAG
- task-per-model rendering
- local DAG test

### P3 - Lineage

Deliverables:

- dbt docs generation
- optional OpenLineage emission strategy
- lineage verification test or artifact

### P4 - Environment and warehouse configuration

Deliverables:

- config loader
- local/dev/staging/prod config files
- secret reference strategy
- environment promotion rules

### P5 - CI/CD and GitOps promotion

Deliverables:

- CI validation pipeline
- DAG import test
- Cosmos render test
- dbt build test
- Feast registry test
- config-only promotion diff proof

---

## Local setup

Prerequisites:

- Git
- `uv`
- Python 3.11 available through `uv`

Install/sync:

```bash
uv sync
```