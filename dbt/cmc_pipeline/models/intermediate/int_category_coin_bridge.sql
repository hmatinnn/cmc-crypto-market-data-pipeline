-- Coin <-> category bridge, latest snapshot only. category_details holds one
-- row per (category, coin) pair per run, so dedupe on that composite key.
--
-- Scoped to int_coins (the map/info-derived coin universe) via inner join:
-- the CMC category endpoint returns ALL member coins regardless of rank, so
-- category_details references thousands of coin_ids we never pulled name/
-- symbol/price data for. Those rows are dropped here -- an unlabeled coin_id
-- with no attributes anywhere in the warehouse isn't useful in a bridge that
-- exists to join back to dim_coins.

with tracked_coins as (
    select coin_id from {{ ref('int_coins') }}
),

category_details as (
    select
        *,
        row_number() over (
            partition by category_id, coin_id order by inserted_at desc
        ) as rn
    from {{ ref('stg_cmc__category_details') }}
)

select
    cd.category_id,
    cd.coin_id,
    cd.last_updated_at,
    cd.inserted_at
from category_details cd
inner join tracked_coins t on cd.coin_id = t.coin_id
where cd.rn = 1
