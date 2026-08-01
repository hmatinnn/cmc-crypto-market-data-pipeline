-- Coin Explorer: current state, one row per coin, with names/logos and
-- pre-computed ratios (FDV/MC, supply utilization, MC/TVL) so Superset
-- charts need no SQL expressions.

select
    f.coin_id,
    d.coin_name,
    d.coin_symbol,
    d.coin_slug,
    d.logo_url,
    f.cmc_rank,
    f.price,
    f.percent_change_1h,
    f.percent_change_24h,
    f.percent_change_7d,
    f.percent_change_30d,
    f.percent_change_60d,
    f.percent_change_90d,
    f.market_cap,
    f.market_cap_dominance_pct,
    f.volume_24h,
    f.volume_change_24h_pct,
    f.cex_volume_24h,
    f.dex_volume_24h,
    f.fully_diluted_market_cap,
    f.fully_diluted_market_cap / nullif(f.market_cap, 0)   as fdv_mc_ratio,
    f.circulating_supply,
    f.total_supply,
    f.max_supply,
    f.is_infinite_supply,
    case
        when f.is_infinite_supply then null
        else f.circulating_supply / nullif(f.max_supply, 0)
    end                                                    as supply_utilization,
    f.tvl,
    f.tvl_ratio,
    f.market_cap / nullif(f.tvl, 0)                        as mc_tvl_ratio,
    f.num_market_pairs,
    f.date_added_at,
    (f.date_added_at >= now() - interval '90 days')        as is_new_coin_90d,
    f.last_updated_at
from {{ ref('fact_coin_market') }} f
left join {{ ref('dim_coins') }} d using (coin_id)
