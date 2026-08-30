{{ config(materialized='table') }}

select
    VendorID as vendor_id,
    tpep_pickup_datetime as pickup_at,
    tpep_dropoff_datetime as dropoff_at,
    PULocationID as pickup_zone_id,
    DOLocationID as dropoff_zone_id,
    trip_distance as trip_distance_miles,
    total_amount,
    passenger_count,
    fare_amount,
    tip_amount
from read_parquet('{{ var("raw_data_path") }}')
where pickup_at is not null
  and dropoff_at is not null
  and dropoff_at > pickup_at
  and PULocationID is not null