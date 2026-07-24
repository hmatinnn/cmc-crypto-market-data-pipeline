-- Latest snapshot per category. categories accumulates a new row per
-- category on every pipeline run, so dedupe to the most recent insert.

with categories as (
    select
        *,
        row_number() over (partition by category_id order by inserted_at desc) as rn
    from {{ ref('stg_cmc__categories') }}
)

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
from categories
where rn = 1
