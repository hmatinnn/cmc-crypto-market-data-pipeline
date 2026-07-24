-- Coin market fact table. One row per coin, latest known market snapshot
-- (supply, rank, price, volume, market cap). Grain: current state, not a
-- historical time series -- for trend queries, go back to the staging
-- layer (stg_cmc__listings_latest / stg_cmc__quotes), which keeps every run.
--
-- Materialized as a view (overrides the olap default of table): fact data
-- changes every pipeline run, and a table only reflects data as of the last
-- `dbt run`, which was going stale between manual runs. As a view it's
-- always live, at the cost of recomputing the join on every query.

{{ config(materialized='view') }}

select
    coin_id,
    is_infinite_supply,
    circulating_supply,
    total_supply,
    max_supply,
    date_added_at,
    num_market_pairs,
    cmc_rank,
    tvl_ratio,
    self_reported_circulating_supply,
    self_reported_market_cap,
    minted_market_cap,
    price,
    volume_24h,
    volume_change_24h_pct,
    cex_volume_24h,
    dex_volume_24h,
    percent_change_1h,
    percent_change_24h,
    percent_change_7d,
    percent_change_30d,
    percent_change_60d,
    percent_change_90d,
    market_cap,
    market_cap_dominance_pct,
    fully_diluted_market_cap,
    tvl,
    last_updated_at,
    inserted_at
from {{ ref('int_coin_market_snapshot') }}
