-- Grain: one row per lead.
select * from {{ ref('int_leads__with_deals') }}
