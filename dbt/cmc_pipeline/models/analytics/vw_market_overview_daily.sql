-- Market Overview: one row per snapshot day, whole-market aggregates.
-- Source is staging (keeps every run) so this is a true time series.
-- Dedupe: if a day has multiple runs (retry/manual trigger), only the
-- latest snapshot per coin per day counts.

with quotes as (

    select
        *,
        row_number() over (
            partition by coin_id, inserted_at::date
            order by inserted_at desc
        ) as rn
    from {{ ref('stg_cmc__quotes') }}

),

daily as (

    select * from quotes where rn = 1

),

ranked as (

    select
        *,
        row_number() over (
            partition by inserted_at::date
            order by market_cap desc nulls last
        ) as mc_rank
    from daily

)

select
    inserted_at::date                                   as snapshot_date,
    sum(market_cap)                                     as total_market_cap,
    sum(volume_24h)                                     as total_volume_24h,
    sum(cex_volume_24h)                                 as total_cex_volume_24h,
    sum(dex_volume_24h)                                 as total_dex_volume_24h,
    sum(dex_volume_24h)
        / nullif(sum(cex_volume_24h) + sum(dex_volume_24h), 0)
                                                        as dex_volume_share,
    max(market_cap_dominance_pct)
        filter (where coin_id = 1)                      as btc_dominance_pct,
    sum(market_cap) filter (where mc_rank <= 10)
        / nullif(sum(market_cap), 0)                    as top10_market_cap_share,
    count(*)                                            as num_coins
from ranked
group by 1
