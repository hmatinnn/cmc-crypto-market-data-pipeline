-- Coin dimension. One row per coin, static/rarely-changing attributes.
-- Materialized as a physical table (see dbt_project.yml) so BI tools
-- (Grafana) can query it directly without recomputing the join chain.

select
    coin_id,
    coin_name,
    coin_symbol,
    coin_slug,
    is_active,
    first_historical_data_at,
    last_historical_data_at,
    coin_category,
    coin_description,
    logo_url,
    date_launched_at
from {{ ref('int_coins') }}
