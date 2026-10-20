with source as (
    select * from {{ source('olist', 'order_items') }}
),

renamed as (
    select
        -- composite key (order_id, order_item_id) -> one single-column key for tests and joins
        order_id || '-' || order_item_id          as order_item_key,
        order_id,
        cast(order_item_id as integer)            as order_item_number,
        product_id,
        seller_id,
        cast(shipping_limit_date as timestamp)    as shipping_limit_at,
        cast(price as decimal(10, 2))             as price_brl,
        cast(freight_value as decimal(10, 2))     as freight_brl,
        _source_file,
        _loaded_at
    from source
)

select * from renamed
