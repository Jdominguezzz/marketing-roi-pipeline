with source as (
    select * from {{ source('olist', 'order_payments') }}
),

renamed as (
    select
        order_id || '-' || payment_sequential      as order_payment_key,
        order_id,
        cast(payment_sequential as integer)        as payment_number,
        payment_type,
        cast(payment_installments as integer)      as installments,
        cast(payment_value as decimal(10, 2))      as payment_value_brl,
        _source_file,
        _loaded_at
    from source
)

select * from renamed
