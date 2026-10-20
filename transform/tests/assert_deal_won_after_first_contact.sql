{{ config(severity = 'warn') }}

-- Contract issue (closed_deals #2): a deal cannot be won before the lead's first contact.
-- Known: 1 row in the source. Severity = warn, so it's reported but doesn't stop the build.

select
    d.lead_id,
    l.first_contact_date,
    d.won_date
from {{ ref('stg_olist__closed_deals') }} as d
inner join {{ ref('stg_olist__leads') }} as l using (lead_id)
where d.won_date < l.first_contact_date
