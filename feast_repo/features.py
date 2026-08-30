import os
from datetime import timedelta

from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float64, Int64

PARQUET_PATH = os.environ.get(
    "FEAST_FEATURE_PARQUET_PATH",
    "var/feast/data/features.parquet",
)

zone = Entity(
    name="pickup_zone",
    join_keys=["pickup_zone_id"],
    description="NYC Taxi pickup zone ID",
)

trip_source = FileSource(
    path=PARQUET_PATH,
    timestamp_field="hour_bucket",
)

trip_features = FeatureView(
    name="trip_features",
    entities=[zone],
    ttl=timedelta(days=2),
    schema=[
        Field(name="trip_count_1h", dtype=Int64),
        Field(name="avg_trip_duration_seconds_1h", dtype=Float64),
        Field(name="p95_trip_duration_seconds_1h", dtype=Float64),
        Field(name="avg_total_amount_1h", dtype=Float64),
        Field(name="avg_trip_distance_miles_1h", dtype=Float64),
    ],
    online=True,
    source=trip_source,
    tags={"team": "platform", "source": "dbt"},
)
