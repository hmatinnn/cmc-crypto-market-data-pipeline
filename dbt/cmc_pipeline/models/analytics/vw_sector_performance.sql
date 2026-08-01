-- Sector/Category performance: one row per category, aggregated from the
-- coins actually tracked in the warehouse (bridge join), so the numbers are
-- consistent with fact_coin_market -- unlike dim_categories' own
-- market_cap/avg_price_change_pct, which CMC computes over ALL member
-- coins including ones outside our top-500 universe.

select
    c.category_id,
    c.category_name,
    c.category_title,
    count(*)                      as num_coins,
    sum(f.market_cap)             as market_cap,
    sum(f.volume_24h)             as volume_24h,
    avg(f.percent_change_24h)     as avg_change_24h_pct,
    avg(f.percent_change_7d)      as avg_change_7d_pct,
    avg(f.percent_change_30d)     as avg_change_30d_pct,
    sum(f.tvl)                    as tvl,
    sum(f.market_cap) / nullif(sum(f.tvl), 0) as mc_tvl_ratio
from {{ ref('bridge_category_coin') }} b
join {{ ref('fact_coin_market') }} f using (coin_id)
join {{ ref('dim_categories') }} c using (category_id)
group by 1, 2, 3
