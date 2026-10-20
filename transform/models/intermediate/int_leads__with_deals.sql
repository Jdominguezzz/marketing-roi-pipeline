-- One row per lead, with its deal if it was won. Grain = lead (8,000 rows).

with leads as (
    select * from {{ ref('stg_olist__leads') }}
),

deals as (
    select * from {{ ref('stg_olist__closed_deals') }}
)

select
    l.lead_id,
    l.channel,
    l.first_contact_date,
    date_trunc('month', l.first_contact_date)::date             as lead_month,
    d.lead_id is not null                                      as is_won,
    d.seller_id,
    d.won_date,
    -- one deal is "won" before first contact (impossible): keep the deal, null the duration
    case
        when d.won_date >= l.first_contact_date
            then date_diff('day', l.first_contact_date, d.won_date)
    end                                                        as days_to_close,
    d.business_segment,
    d.lead_type,
    d.business_type
from leads as l
left join deals as d using (lead_id)
