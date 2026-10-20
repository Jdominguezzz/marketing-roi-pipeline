-- Grain: one row per channel x lead month (cohort = month of first contact).
-- CAC uses ALL won deals. 3-month LTV only uses deals that had 3 full months to sell
-- before the observation end (right-censoring, see docs/data_contracts.md).

with months as (
    select cast(m as date) as lead_month
    from generate_series(date '2017-06-01', date '2018-05-01', interval 1 month) as t(m)
),

spine as (
    select c.channel, m.lead_month from {{ ref('dim_channel') }} as c cross join months as m
),

leads as (
    select
        channel,
        lead_month,
        count(*)                                    as leads,
        count(*) filter (where is_won)              as deals,
        count(*) filter (
            where is_won
              and won_date + interval 3 month <= date '{{ var("observation_end_date") }}' + interval 1 day
        )                                           as deals_ltv_eligible
    from {{ ref('fct_leads') }}
    group by 1, 2
),

spend as (
    select channel, spend_month as lead_month, sum(spend_brl) as spend_brl, sum(spend_eur) as spend_eur
    from {{ ref('fct_ad_spend_daily') }}
    group by 1, 2
),

revenue_m3 as (
    select
        l.channel,
        l.lead_month,
        sum(r.olist_revenue_brl) as revenue_m3_brl,
        sum(r.olist_revenue_eur) as revenue_m3_eur
    from {{ ref('fct_seller_revenue') }} as r
    inner join {{ ref('fct_leads') }} as l using (lead_id)
    where r.purchase_date < r.won_date + interval 3 month
      and r.won_date + interval 3 month <= date '{{ var("observation_end_date") }}' + interval 1 day
    group by 1, 2
),

joined as (
    select
        s.channel || '-' || cast(s.lead_month as varchar)  as channel_month_key,
        s.channel,
        s.lead_month,
        coalesce(l.leads, 0)                                as leads,
        coalesce(l.deals, 0)                                as deals,
        coalesce(l.deals_ltv_eligible, 0)                   as deals_ltv_eligible,
        coalesce(sp.spend_brl, 0)                           as spend_brl,
        coalesce(sp.spend_eur, 0)                           as spend_eur,
        coalesce(r.revenue_m3_brl, 0)                       as revenue_m3_brl,
        coalesce(r.revenue_m3_eur, 0)                       as revenue_m3_eur
    from spine as s
    left join leads as l using (channel, lead_month)
    left join spend as sp using (channel, lead_month)
    left join revenue_m3 as r using (channel, lead_month)
)

select
    *,
    deals / nullif(leads, 0)                              as conversion_rate,
    nullif(spend_eur, 0) / nullif(leads, 0)              as cpl_eur,   -- NULL, not 0, when no spend
    nullif(spend_eur, 0) / nullif(deals, 0)              as cac_eur,
    revenue_m3_eur / nullif(deals_ltv_eligible, 0)        as ltv_m3_per_deal_eur
from joined
