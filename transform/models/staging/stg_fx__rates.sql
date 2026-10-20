-- One row per ECB publication day. Weekends and holidays are missing on purpose:
-- the as-of join in intermediate fills them with the latest earlier rate.

with source as (
    select * from {{ source('fx', 'fx_rates') }}
)

select
    cast(rate_date as date)            as rate_date,
    cast(brl_eur as decimal(12, 6))    as brl_to_eur,
    base                               as base_currency,
    _source_file,
    _loaded_at
from source
