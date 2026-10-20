-- One row per delivered order item sold by a seller acquired through the funnel,
-- with how long after acquisition the sale happened. Only sales up to the observation end.

with deals as (
    select lead_id, seller_id, won_date from {{ ref('stg_olist__closed_deals') }}
),

items as (
    select * from {{ ref('stg_olist__order_items') }}
),

orders as (
    select order_id, order_status, purchase_date from {{ ref('stg_olist__orders') }}
),

fx as (
    select calendar_date, brl_to_eur from {{ ref('int_fx__daily') }}
)

select
    i.order_item_key,
    d.lead_id,
    d.seller_id,
    d.won_date,
    o.purchase_date,
    date_diff('day', d.won_date, o.purchase_date)                            as days_since_won,
    i.price_brl                                                              as gmv_brl,
    i.price_brl * {{ var('take_rate') }}                                     as olist_revenue_brl,
    i.price_brl * {{ var('take_rate') }} * fx.brl_to_eur                     as olist_revenue_eur
from items as i
inner join deals as d using (seller_id)
inner join orders as o using (order_id)
left join fx on fx.calendar_date = o.purchase_date
where o.order_status = 'delivered'
  and o.purchase_date <= date '{{ var("observation_end_date") }}'
