import os
from pathlib import Path

import duckdb

# Absolute paths injected by docker-compose; relative fallbacks for local dev
DB_PATH = os.environ.get("DUCKDB_PATH", "var/duckdb/feature_platform.duckdb")
EXPORT_PATH = os.environ.get(
    "FEAST_FEATURE_PARQUET_PATH",
    "var/feast/data/features.parquet",
)


def main():
    Path(EXPORT_PATH).parent.mkdir(parents=True, exist_ok=True)

    if not Path(DB_PATH).exists():
        raise FileNotFoundError(f"DuckDB not found at {DB_PATH}. Run dbt build first.")

    con = duckdb.connect(DB_PATH, read_only=True)
    print(f"Exporting feature mart to {EXPORT_PATH}...")
    con.execute(f"""
        COPY (
            SELECT
                pickup_zone_id,
                hour_bucket,
                trip_count_1h,
                avg_trip_duration_seconds_1h,
                p95_trip_duration_seconds_1h,
                avg_total_amount_1h,
                avg_trip_distance_miles_1h
            FROM feature_pickup_zone_hourly
        ) TO '{EXPORT_PATH}' (FORMAT PARQUET)
    """)
    con.close()
    print("Export complete.")


if __name__ == "__main__":
    main()
