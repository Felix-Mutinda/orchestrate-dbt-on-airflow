select
    LocationID as zone_id,
    Borough as borough,
    Zone as zone_name
from {{ ref('taxi_zone_lookup') }}