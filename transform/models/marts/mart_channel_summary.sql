-- Grain: one row per channel, all cohorts Jul 2017 - May 2018 together.
-- June 2017 is excluded: leads start on 14 June but spend starts on 1 June (partial month).
-- This is the table behind the headline finding.

with roi as (
    select * from {{ ref('mart_channel_roi') }}
    where lead_month >= date '2017-07-01'
),

totals as (
    select
        channel,
        sum(leads)              as leads,
        sum(deals)              as deals,
        sum(deals_ltv_eligible) as deals_ltv_eligible,
        sum(spend_eur)          as spend_eur,
        sum(revenue_m3_eur)     as revenue_m3_eur
    from roi
    group by 1
)

select
    t.channel,
    c.display_name,
    c.channel_group,
    c.is_paid,
    t.leads,
    t.deals,
    t.deals / nullif(t.leads, 0)                                       as conversion_rate,
    t.spend_eur,
    nullif(t.spend_eur, 0) / nullif(t.leads, 0)                       as cpl_eur,   -- NULL for organic
    nullif(t.spend_eur, 0) / nullif(t.deals, 0)                       as cac_eur,
    t.deals_ltv_eligible,
    t.revenue_m3_eur / nullif(t.deals_ltv_eligible, 0)                 as ltv_m3_per_deal_eur,
    (t.revenue_m3_eur / nullif(t.deals_ltv_eligible, 0))
        / (nullif(t.spend_eur, 0) / nullif(t.deals, 0))                as ltv_to_cac_m3
from totals as t
inner join {{ ref('dim_channel') }} as c using (channel)
