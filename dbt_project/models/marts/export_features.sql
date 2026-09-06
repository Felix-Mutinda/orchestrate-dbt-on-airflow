
{{ config(
    materialized='external',
    location=env_var('FEAST_FEATURE_PARQUET_PATH', 'var/feast/data/features.parquet')
) }}

select 
    pickup_zone_id,
    hour_bucket,
    trip_count_1h,
    avg_trip_duration_seconds_1h,
    p95_trip_duration_seconds_1h,
    avg_total_amount_1h,
    avg_trip_distance_miles_1h
from {{ ref('feature_pickup_zone_hourly') }}