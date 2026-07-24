with source as (
    select * from {{ source('cmc_raw', 'map') }}
),

renamed as (
    select
        id::bigint                            as coin_id,
        name::varchar                         as coin_name,
        symbol::varchar                        as coin_symbol,
        slug::varchar                           as coin_slug,
        (is_active = 1)                          as is_active,
        first_historical_data::timestamp          as first_historical_data_at,
        last_historical_data::timestamp            as last_historical_data_at
    from source
)

select * from renamed
