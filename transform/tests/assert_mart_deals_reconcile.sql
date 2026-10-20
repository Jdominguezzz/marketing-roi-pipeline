-- Reconciliation: deals in the mart = won deals in the leads fact (842).
select m.total as mart_deals, f.total as fact_deals
from (select sum(deals) as total from {{ ref('mart_channel_roi') }}) as m,
     (select count(*) filter (where is_won) as total from {{ ref('fct_leads') }}) as f
where m.total <> f.total
