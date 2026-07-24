-- Coin dimension: static/rarely-changing attributes (1 row per coin).
-- map and info are both loaded fresh each run with no historical duplication,
-- so this is a straight 1:1 join.

with map as (
    select * from {{ ref('stg_cmc__map') }}
),

info as (
    select * from {{ ref('stg_cmc__info') }}
),

joined as (
    select
        map.coin_id,
        map.coin_name,
        map.coin_symbol,
        map.coin_slug,
        map.is_active,
        map.first_historical_data_at,
        map.last_historical_data_at,
        info.coin_category,
        info.coin_description,
        info.logo_url,
        info.date_launched_at
    from map
    left join info on map.coin_id = info.coin_id
)

select * from joined
