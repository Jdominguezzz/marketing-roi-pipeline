select
    calendar_date                                  as date_day,
    date_trunc('month', calendar_date)::date       as month_start,
    year(calendar_date)                            as year,
    month(calendar_date)                           as month,
    dayofweek(calendar_date)                       as day_of_week,
    dayofweek(calendar_date) in (0, 6)             as is_weekend,
    brl_to_eur
from {{ ref('int_fx__daily') }}
