with source as (
    select * from {{ source('cmc_raw', 'category_details') }}
),

renamed as (
    select
        id::varchar                    as category_id,
        name::varchar                   as category_name,
        title::varchar                   as category_title,
        description::text                 as category_description,
        volume::numeric                    as volume_24h,
        num_tokens::int                     as num_tokens,
        last_updated::timestamp              as last_updated_at,
        avg_price_change::numeric             as avg_price_change_pct,
        market_cap::numeric                    as market_cap,
        market_cap_change::numeric              as market_cap_change_pct,
        volume_change::numeric                   as volume_change_pct,
        coins_id::bigint                           as coin_id,
        inserted_at::timestamp                     as inserted_at
    from source
)

select * from renamed
