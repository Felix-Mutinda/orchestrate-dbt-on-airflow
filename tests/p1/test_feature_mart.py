from pathlib import Path

import duckdb
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = REPO_ROOT / "var" / "duckdb" / "feature_platform.duckdb"


@pytest.fixture(scope="module")
def con():
    if not DB_PATH.exists():
        pytest.skip("DuckDB database not found. Run `make dbt-build` first.")
    return duckdb.connect(str(DB_PATH), read_only=True)


def test_feature_mart_has_data(con):
    df = con.execute("SELECT count(*) as cnt FROM feature_pickup_zone_hourly").fetchdf()
    # With the full dataset, we expect thousands of hourly zone buckets
    assert df["cnt"][0] > 1000


def test_feature_mart_no_null_zones(con):
    df = con.execute(
        "SELECT count(*) as cnt FROM feature_pickup_zone_hourly WHERE pickup_zone_id IS NULL"
    ).fetchdf()
    assert df["cnt"][0] == 0


def test_feature_mart_positive_trip_counts(con):
    df = con.execute(
        "SELECT min(trip_count_1h) as min_cnt FROM feature_pickup_zone_hourly"
    ).fetchdf()
    assert df["min_cnt"][0] >= 1
