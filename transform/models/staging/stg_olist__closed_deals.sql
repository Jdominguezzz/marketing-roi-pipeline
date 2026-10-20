with source as (
    select * from {{ source('olist', 'closed_deals') }}
),

renamed as (
    select
        mql_id                                                    as lead_id,
        seller_id,
        sdr_id,
        sr_id,
        cast(won_date as timestamp)                               as won_at,
        cast(won_date as date)                                    as won_date,
        business_segment,
        lead_type,
        lead_behaviour_profile,
        business_type,
        cast(has_company as boolean)                              as has_company,
        cast(has_gtin as boolean)                                 as has_gtin,
        average_stock,
        cast(declared_product_catalog_size as double)             as declared_product_catalog_size,
        -- 94.7% of values are 0: 0 means "not filled in", so it becomes NULL (contract issue 1)
        nullif(cast(declared_monthly_revenue as decimal(18, 2)), 0) as declared_monthly_revenue,
        _source_file,
        _loaded_at
    from source
)

select * from renamed
