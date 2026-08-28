with trips as (
    select * from {{ ref('fct_trips') }}
)

select
    pickup_hour_bucket as hour_bucket,
    pickup_zone_id,
    count(*) as trip_count_1h,
    avg(trip_duration_seconds) as avg_trip_duration_seconds_1h,
    quantile_cont(trip_duration_seconds, 0.95) as p95_trip_duration_seconds_1h,
    avg(total_amount) as avg_total_amount_1h,
    avg(trip_distance_miles) as avg_trip_distance_miles_1h
from trips
group by 1, 2