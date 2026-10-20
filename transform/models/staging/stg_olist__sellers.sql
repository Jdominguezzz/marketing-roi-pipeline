with source as (
    select * from {{ source('olist', 'sellers') }}
),

renamed as (
    select
        seller_id,
        seller_zip_code_prefix      as zip_code_prefix, -- stays VARCHAR: leading zeros
        {{ clean_city('seller_city') }} as city,
        upper(trim(seller_state))   as state,
        _source_file,
        _loaded_at
    from source
)

select * from renamed
