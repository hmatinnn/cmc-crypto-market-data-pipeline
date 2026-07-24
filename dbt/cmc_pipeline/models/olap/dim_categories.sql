-- Category dimension. One row per category, latest known attributes
-- (volume/market_cap are "as of last run" snapshot values, not historical).

select
    category_id,
    category_name,
    category_title,
    category_description,
    volume_24h,
    num_tokens,
    avg_price_change_pct,
    market_cap,
    market_cap_change_pct,
    volume_change_pct,
    last_updated_at,
    inserted_at
from {{ ref('int_category_snapshot') }}
