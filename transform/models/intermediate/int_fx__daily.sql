-- One row per calendar day with the BRL->EUR rate in force that day.
-- ECB publishes no rate on weekends/holidays, so an AS-OF join takes the latest earlier rate.

with calendar as (
    select cast(day as date) as calendar_date
    from generate_series(date '2016-09-01', date '2018-10-31', interval 1 day) as t(day)
),

rates as (
    select rate_date, brl_to_eur from {{ ref('stg_fx__rates') }}
)

select
    c.calendar_date,
    r.brl_to_eur,
    r.rate_date                          as rate_published_date,
    c.calendar_date <> r.rate_date       as is_carried_forward
from calendar as c
asof left join rates as r
    on c.calendar_date >= r.rate_date
