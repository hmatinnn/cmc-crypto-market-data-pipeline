with source as (
    select * from {{ source('cmc_raw', 'quotes') }}
),

renamed as (
    select
        id::bigint                               as coin_id,
        name::varchar                            as coin_name,
        symbol::varchar                          as coin_symbol,
        slug::varchar                            as coin_slug,
        (is_fiat = 1)                            as is_fiat,
        quote_id::bigint                         as quote_currency_id,
        quote_symbol::varchar                    as quote_currency_symbol,
        quote_price::numeric                     as price,
        quote_volume_24h::numeric                as volume_24h,
        quote_volume_change_24h::numeric         as volume_change_24h_pct,
        quote_cex_volume_24h::numeric            as cex_volume_24h,
        quote_dex_volume_24h::numeric            as dex_volume_24h,
        quote_percent_change_1h::numeric         as percent_change_1h,
        quote_percent_change_24h::numeric        as percent_change_24h,
        quote_percent_change_7d::numeric         as percent_change_7d,
        quote_percent_change_30d::numeric        as percent_change_30d,
        quote_percent_change_60d::numeric        as percent_change_60d,
        quote_percent_change_90d::numeric        as percent_change_90d,
        quote_market_cap::numeric                as market_cap,
        quote_market_cap_dominance::numeric      as market_cap_dominance_pct,
        quote_fully_diluted_market_cap::numeric  as fully_diluted_market_cap,
        quote_minted_market_cap::numeric         as minted_market_cap,
        quote_tvl::numeric                       as tvl,
        quote_last_updated::timestamp            as last_updated_at,
        inserted_at::timestamp                   as inserted_at
    from source
)

select * from renamed
