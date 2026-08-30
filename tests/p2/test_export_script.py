from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXPORT_SCRIPT = REPO_ROOT / "scripts" / "export_features.py"


def test_export_script_exists():
    assert EXPORT_SCRIPT.exists(), "scripts/export_features.py must exist"


def test_export_script_is_valid_python():
    """Verify the export script has no syntax errors."""
    source = EXPORT_SCRIPT.read_text()
    try:
        import ast

        ast.parse(source)
    except SyntaxError as e:
        pytest.fail(f"Export script has syntax error: {e}")


def test_export_script_uses_env_vars():
    """Export script should use env vars for path-agnostic execution."""
    source = EXPORT_SCRIPT.read_text()
    assert "DUCKDB_PATH" in source, "Export script should use DUCKDB_PATH env var"
    assert "FEAST_FEATURE_PARQUET_PATH" in source, (
        "Export script should use FEAST_FEATURE_PARQUET_PATH env var"
    )


def test_export_script_creates_parent_directories():
    """Export script should create parent dirs before writing."""
    source = EXPORT_SCRIPT.read_text()
    assert "mkdir" in source, "Export script should create parent directories"


def test_export_script_uses_read_only_connection():
    """Export script should open DuckDB in read-only mode."""
    source = EXPORT_SCRIPT.read_text()
    assert "read_only=True" in source, (
        "Export script should use read-only DuckDB connection"
    )
