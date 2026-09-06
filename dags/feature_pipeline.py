import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from cosmos import DbtTaskGroup, ProjectConfig, ProfileConfig, ExecutionConfig, RenderConfig
from cosmos.constants import ExecutionMode, TestBehavior

REPO_ROOT = Path("/opt/airflow")

# 1. Load the centralized config
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from config import get_config

config = get_config()

# 2. Inject warehouse env vars for dbt
# Cosmos passes these directly to the dbt subprocess
dbt_env_vars = {
    "ENV_NAME": config.env_name,
    "WAREHOUSE_PATH": config.warehouse.path or "",
    "WAREHOUSE_SCHEMA": config.warehouse.schema_name,
    "FEAST_FEATURE_PARQUET_PATH": "/opt/airflow/var/feast/data/features.parquet", 
}

# Inject Feast env vars globally for this DAG process
os.environ["FEAST_ONLINE_STORE_TYPE"] = config.feast.online_store_type
os.environ["FEAST_ONLINE_STORE_PATH"] = config.feast.online_store_path

project_config = ProjectConfig(dbt_project_path=str(REPO_ROOT / "dbt_project"))
profile_config = ProfileConfig(
    profile_name="feature_platform",
    target_name=config.env_name, # Dynamically switches local/dev/prod
    profiles_yml_filepath=str(REPO_ROOT / "dbt_project" / "profiles.yml"),
)
render_config = RenderConfig(emit_datasets=True, test_behavior=TestBehavior.AFTER_EACH)

# 3. Helper function to export features (used dbt-duckdb external materialization instead)
def export_features_to_parquet():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from export_features import main as export_main
    export_main()

# 4. Helper function for Feast
def feast_apply_and_materialize():
    from feast import FeatureStore
    from feast.repo_operations import apply_total, parse_repo

    repo_root_path = Path(REPO_ROOT)
    feast_repo_path = repo_root_path / "feast_repo"
    if str(repo_root_path) not in sys.path:
        sys.path.insert(0, str(repo_root_path))
    store = FeatureStore(repo_path=str(feast_repo_path))
    
    print(f"Applying Feast registry for {config.env_name}...")
    if str(feast_repo_path) not in sys.path:
            sys.path.insert(0, str(feast_repo_path))
    repo_config = store.config
    repo_objects = parse_repo(Path(feast_repo_path)) 
    apply_total(repo_config, feast_repo_path, False)
    
    print(f"Materializing from {config.feast.materialize_start} to {config.feast.materialize_end}...")
    store.materialize(
        start_date=datetime.fromisoformat(config.feast.materialize_start), 
        end_date=datetime.fromisoformat(config.feast.materialize_end)
    )

# 5. DAG Definition
default_args = {"owner": "platform", "retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="feature_platform_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["dbt", "cosmos", "feast"],
    max_active_tasks=config.max_active_tasks, # Dynamically set concurrency
) as dag:

    dbt_pipeline = DbtTaskGroup(
        group_id="dbt_feature_transformations",
        project_config=project_config,
        profile_config=profile_config,
        render_config=render_config,
        execution_config=ExecutionConfig(execution_mode=ExecutionMode.LOCAL),
        operator_args={"install_deps": False, "env": dbt_env_vars}, # Pass env vars to dbt
    )

    feast_task = PythonOperator(
        task_id="feast_apply_and_materialize",
        python_callable=feast_apply_and_materialize,
    )

    dbt_pipeline >> feast_task