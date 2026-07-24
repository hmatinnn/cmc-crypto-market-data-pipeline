-- Singular test: (category_id, coin_id) must be unique in bridge_category_coin.
-- Returns offending rows; dbt fails the test if any rows come back.

select
    category_id,
    coin_id,
    count(*) as row_count
from {{ ref('bridge_category_coin') }}
group by category_id, coin_id
having count(*) > 1
