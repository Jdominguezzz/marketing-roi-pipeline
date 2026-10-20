-- Reconciliation: every euro of spend in staging must appear exactly once in the ROI mart.
-- A fan-out join would duplicate spend; a missing spine row would drop it. Tolerance: 1 cent.

with staging as (
    select sum(spend_eur) as total from {{ ref('fct_ad_spend_daily') }}
),

mart as (
    select sum(spend_eur) as total from {{ ref('mart_channel_roi') }}
)

select staging.total as staging_total, mart.total as mart_total
from staging, mart
where abs(staging.total - mart.total) > 0.01
