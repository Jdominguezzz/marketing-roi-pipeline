-- Grain: one row per paid channel per day. SIMULATED spend (ADR-003).
select
    s.spend_key,
    s.spend_date,
    date_trunc('month', s.spend_date)::date   as spend_month,
    s.channel,
    s.spend_brl,
    s.spend_brl * fx.brl_to_eur               as spend_eur
from {{ ref('stg_ads__spend') }} as s
left join {{ ref('int_fx__daily') }} as fx on fx.calendar_date = s.spend_date
