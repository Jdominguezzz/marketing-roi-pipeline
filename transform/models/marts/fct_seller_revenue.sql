-- Grain: one row per delivered order item of a funnel-acquired seller.
select * from {{ ref('int_seller__revenue') }}
