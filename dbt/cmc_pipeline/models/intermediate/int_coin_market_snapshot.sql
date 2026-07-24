with tracked_coins as (
    select coin_id from {{ ref('int_coins') }}
),

listings as (
    select
        *,
        row_number() over (partition by coin_id order by inserted_at desc) as rn
    from {{ ref('stg_cmc__listings_latest') }}
),

quotes as (
    select
        *,
        row_number() over (partition by coin_id order by inserted_at desc) as rn
    from {{ ref('stg_cmc__quotes') }}
),

listings_latest_snapshot as (
    select * from listings where rn = 1
),

quotes_latest_snapshot as (
    select * from quotes where rn = 1
),

joined as (
    select
        l.coin_id,
        l.is_infinite_supply,
        l.circulating_supply,
        l.total_supply,
        l.max_supply,
        l.date_added_at,
        l.num_market_pairs,
        l.cmc_rank,
        l.tvl_ratio,
        l.self_reported_circulating_supply,
        l.self_reported_market_cap,
        l.minted_market_cap,
        q.price,
        q.volume_24h,
        q.volume_change_24h_pct,
        q.cex_volume_24h,
        q.dex_volume_24h,
        q.percent_change_1h,
        q.percent_change_24h,
        q.percent_change_7d,
        q.percent_change_30d,
        q.percent_change_60d,
        q.percent_change_90d,
        q.market_cap,
        q.market_cap_dominance_pct,
        q.fully_diluted_market_cap,
        q.tvl,
        greatest(l.last_updated_at, q.last_updated_at) as last_updated_at,
        greatest(l.inserted_at, q.inserted_at)          as inserted_at
    from listings_latest_snapshot l
    inner join tracked_coins t on l.coin_id = t.coin_id
    left join quotes_latest_snapshot q on l.coin_id = q.coin_id
)

select * from joined
