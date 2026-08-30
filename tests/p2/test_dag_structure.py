import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DAG_PATH = REPO_ROOT / "dags" / "feature_pipeline.py"


@pytest.fixture(scope="module")
def dag_source():
    if not DAG_PATH.exists():
        pytest.skip("dags/feature_pipeline.py not found")
    return DAG_PATH.read_text()


@pytest.fixture(scope="module")
def dag_ast(dag_source):
    return ast.parse(dag_source)


def test_dag_file_exists():
    assert DAG_PATH.exists(), "dags/feature_pipeline.py must exist"


def test_dag_file_is_valid_python(dag_source):
    """Verify the DAG file has no syntax errors."""
    try:
        ast.parse(dag_source)
    except SyntaxError as e:
        pytest.fail(f"DAG file has syntax error: {e}")


def test_dag_defines_feature_platform_pipeline(dag_source):
    assert "feature_platform_pipeline" in dag_source, (
        "DAG must define feature_platform_pipeline"
    )


def test_dag_uses_cosmos_dbt_task_group(dag_source):
    assert "DbtTaskGroup" in dag_source, "DAG must use Cosmos DbtTaskGroup"


def test_dag_has_export_task(dag_source):
    assert "export_features_to_parquet" in dag_source, (
        "DAG must have Parquet export task"
    )


def test_dag_has_feast_task(dag_source):
    assert "feast_apply_and_materialize" in dag_source, (
        "DAG must have Feast materialization task"
    )


def test_dag_sets_max_active_tasks(dag_source):
    """DuckDB single-writer lock requires serialized execution."""
    assert "max_active_tasks" in dag_source, (
        "DAG must set max_active_tasks=1 to respect DuckDB single-writer lock"
    )


def test_dag_imports_inside_functions(dag_source):
    """Airflow 3 best practice: heavy imports inside task functions, not top-level."""
    # Check that FeatureStore is NOT imported at top level
    lines = dag_source.split("\n")
    top_level_imports = []
    for line in lines:
        stripped = line.strip()

        # 1. Check if the line actually imports feast
        is_feast_import = stripped.startswith(("from feast", "import feast"))

        # 2. Check if it has NO leading whitespace (meaning it's top-level)
        is_top_level = not (line.startswith((" ", "\t")))

        if is_feast_import and is_top_level:
            top_level_imports.append(stripped)

    assert len(top_level_imports) == 0, (
        f"Feast imports should be inside functions, not top-level: {top_level_imports}"
    )


def test_dag_task_dependency_chain(dag_source):
    """Verify the DAG has the correct dependency chain: dbt >> export >> feast."""
    assert ">>" in dag_source, "DAG must define task dependencies"
    # Check that export is between dbt and feast
    assert "dbt_pipeline >> export_task >> feast_task" in dag_source, (
        "DAG must chain: dbt_pipeline >> export_task >> feast_task"
    )
