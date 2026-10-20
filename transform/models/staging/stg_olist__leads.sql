with source as (
    select * from {{ source('olist', 'marketing_qualified_leads') }}
),

renamed as (
    select
        mql_id                                                as lead_id,
        cast(first_contact_date as date)                      as first_contact_date,
        landing_page_id,
        coalesce(nullif(lower(trim(origin)), ''), 'unknown')  as channel,
        _source_file,
        _loaded_at
    from source
)

select * from renamed
