with source as (
    select * from {{ source('olist', 'customers') }}
),

renamed as (
    select
        customer_id,                                  -- one per ORDER, not per person (contract issue 1)
        customer_unique_id         as person_id,      -- the real person
        customer_zip_code_prefix   as zip_code_prefix, -- stays VARCHAR: leading zeros
        {{ clean_city('customer_city') }} as city,
        upper(trim(customer_state)) as state,
        _source_file,
        _loaded_at
    from source
)

select * from renamed
