-- SIMULATED source (ADR-003). Fixes the 3 injected delivery problems:
--   1. renamed field  -> coalesce(spend, cost)
--   2. duplicate day  -> keep one row per (spend_date, channel): the latest delivery wins
--   3. late file      -> nothing to fix: we key on the event date, not the delivery date

with source as (
    select * from {{ source('ads', 'ad_spend') }}
),

standardised as (
    select
        cast("date" as date)                          as spend_date,
        lower(trim(channel))                          as channel,
        cast(coalesce(spend, cost) as decimal(12, 2)) as spend_brl,
        upper(currency)                               as currency,
        cast(ingest_date as date)                     as delivered_date,
        _source_file,
        _loaded_at
    from source
),

deduplicated as (
    select *
    from standardised
    qualify row_number() over (
        partition by spend_date, channel
        order by delivered_date desc, _source_file desc
    ) = 1
)

select
    channel || '-' || cast(spend_date as varchar) as spend_key,
    *
from deduplicated
