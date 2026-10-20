-- Every calendar day between the first and last spend date must have spend for every channel.
-- Would catch a late file that never arrived, or a dedupe that dropped too much.

with bounds as (
    select min(spend_date) as first_day, max(spend_date) as last_day
    from {{ ref('stg_ads__spend') }}
),

calendar as (
    select cast(day as date) as spend_date
    from bounds, generate_series(first_day, last_day, interval 1 day) as t(day)
),

channels as (
    select distinct channel from {{ ref('stg_ads__spend') }}
),

expected as (
    select c.spend_date, ch.channel from calendar c cross join channels ch
)

select e.*
from expected e
left join {{ ref('stg_ads__spend') }} s using (spend_date, channel)
where s.spend_key is null
