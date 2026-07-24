with source as (
    select * from {{ source('cmc_raw', 'listings_latest') }}
),

renamed as (
    select
        id::bigint                                  as coin_id,
        infinite_supply::boolean                    as is_infinite_supply,
        circulating_supply::numeric                 as circulating_supply,
        total_supply::numeric                       as total_supply,
        max_supply::numeric                         as max_supply,
        date_added::timestamp                       as date_added_at,
        num_market_pairs::int                       as num_market_pairs,
        cmc_rank::int                                as cmc_rank,
        last_updated::timestamp                     as last_updated_at,
        tvl_ratio::numeric                          as tvl_ratio,
        self_reported_circulating_supply::numeric   as self_reported_circulating_supply,
        self_reported_market_cap::numeric           as self_reported_market_cap,
        minted_market_cap::numeric                  as minted_market_cap,
        inserted_at::timestamp                      as inserted_at
    from source
)

select * from renamed
