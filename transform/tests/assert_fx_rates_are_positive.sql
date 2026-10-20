select * from {{ ref('stg_fx__rates') }} where brl_to_eur <= 0
