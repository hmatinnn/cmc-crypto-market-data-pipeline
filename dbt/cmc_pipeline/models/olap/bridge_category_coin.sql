-- Many-to-many bridge: which coins belong to which categories, latest
-- snapshot only. Join to dim_coins / dim_categories for descriptive
-- attributes -- no attribute duplication lives here.

select
    category_id,
    coin_id,
    last_updated_at,
    inserted_at
from {{ ref('int_category_coin_bridge') }}
