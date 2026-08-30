from datetime import UTC, datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from cosmos import (
    DbtTaskGroup,
    ExecutionConfig,
    ProfileConfig,
    ProjectConfig,
    RenderConfig,
)
from cosmos.constants import ExecutionMode, TestBehavior

REPO_ROOT = Path(__file__).resolve().parent.parent

# Cosmos Configurations
project_config = ProjectConfig(
    dbt_project_path=str(REPO_ROOT / "dbt_project"),
)

profile_config = ProfileConfig(
    profile_name="feature_platform",
    target_name="local",
    profiles_yml_filepath=str(REPO_ROOT / "dbt_project" / "profiles.yml"),
)

render_config = RenderConfig(
    emit_datasets=True,
    test_behavior=TestBehavior.AFTER_EACH,
)


def export_features_to_parquet():
    """Export the dbt DuckDB feature mart to Parquet for Feast."""
    import sys

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from export_features import main as export_main

    export_main()


def feast_apply_and_materialize():
    import sys
    from datetime import UTC, datetime
    from pathlib import Path

    from feast import FeatureStore
    from feast.repo_operations import apply_total, parse_repo

    repo_root_path = Path(REPO_ROOT)
    feast_repo_path = repo_root_path / "feast_repo"

    if str(repo_root_path) not in sys.path:
        sys.path.insert(0, str(repo_root_path))

    if str(feast_repo_path) not in sys.path:
        sys.path.insert(0, str(feast_repo_path))

    # Initialize the FeatureStore object pointing to our repo
    store = FeatureStore(repo_path=str(feast_repo_path))

    # 1. Apply registry by scanning the repo files
    print("Applying Feast registry...")
    repo_config = store.config

    # Parse the repo to get the objects (entities, feature views, etc.) defined in the repo
    _repo_objects = parse_repo(feast_repo_path)

    apply_total(repo_config, feast_repo_path, False)

    # 2. Materialize to online store
    print("Materializing features...")
    store.materialize(
        start_date=datetime(2024, 1, 1, tzinfo=UTC),
        end_date=datetime(2026, 6, 1, tzinfo=UTC),
    )

    print("Feast materialization complete.")


default_args = {
    "owner": "platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with (
    DAG(
        dag_id="feature_platform_pipeline",
        start_date=datetime(2024, 1, 1, tzinfo=UTC),
        schedule="@daily",
        catchup=False,
        default_args=default_args,
        max_active_tasks=1,  # <--- CRITICAL FOR LOCAL DUCKDB: Prevents concurrent write locks
        tags=["dbt", "cosmos", "feast", "feature-platform"],
    ) as dag
):
    # 1. Cosmos renders dbt models into individual Airflow tasks
    dbt_pipeline = DbtTaskGroup(
        group_id="dbt_feature_transformations",
        project_config=project_config,
        profile_config=profile_config,
        render_config=render_config,
        execution_config=ExecutionConfig(execution_mode=ExecutionMode.LOCAL),
    )

    # 2. Export features from DuckDB to Parquet for Feast
    export_task = PythonOperator(
        task_id="export_features_to_parquet",
        python_callable=export_features_to_parquet,
    )

    # 3. Apply Feast registry and materialize to online store
    feast_task = PythonOperator(
        task_id="feast_apply_and_materialize",
        python_callable=feast_apply_and_materialize,
    )

    # Define dependencies: dbt must succeed before Feast materializes
    dbt_pipeline >> export_task >> feast_task
