with trips as (
    select * from {{ ref('stg_yellow_trips') }}
)

select
    md5(
        coalesce(cast(vendor_id as varchar), '') || '-' ||
        coalesce(cast(pickup_at as varchar), '') || '-' || 
        coalesce(cast(dropoff_at as varchar), '') || '-' || 
        coalesce(cast(pickup_zone_id as varchar), '') || '-' || 
        coalesce(cast(dropoff_zone_id as varchar), '') || '-' ||
        coalesce(cast(trip_distance_miles as varchar), '') || '-' ||
        coalesce(cast(total_amount as varchar), '')
    ) as trip_id,
    pickup_at,
    dropoff_at,
    date_trunc('hour', pickup_at) as pickup_hour_bucket,
    pickup_zone_id,
    dropoff_zone_id,
    trip_distance_miles,
    total_amount,
    passenger_count,
    date_diff('second', pickup_at, dropoff_at) as trip_duration_seconds
from trips