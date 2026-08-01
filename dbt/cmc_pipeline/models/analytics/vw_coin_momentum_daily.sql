-- Momentum: one row per coin per snapshot day, with rank movement vs the
-- previous snapshot (lag window). rank_change > 0 = moved UP the ranking.
-- entered_top500 / left-side analysis: prev_cmc_rank is null for a coin's
-- first appearance.
--
-- Names: coalesce(dim_coins, stg_cmc__quotes). dim_coins is rebuilt from the
-- MONTHLY map/info fetch, so coins that enter the top-500 mid-month aren't in
-- it yet and were showing as N/A in Superset. The daily quotes staging carries
-- name/symbol for every listed coin, so it fills the gap until the next
-- monthly refresh.
--
-- prev_snapshot_date: lag() takes a coin's previous APPEARANCE, which for a
-- coin re-entering the top-500 after a long absence can be weeks ago --
-- making rank_change look like a one-day jump. Exposing the date lets
-- consumers see/filter that (e.g. prev_snapshot_date = yesterday for strict
-- day-over-day movers).

with listings as (

    select
        *,
        row_number() over (
            partition by coin_id, inserted_at::date
            order by inserted_at desc
        ) as rn
    from {{ ref('stg_cmc__listings_latest') }}

),

listings_daily as (

    select * from listings where rn = 1

),

quotes as (

    select
        *,
        row_number() over (
            partition by coin_id, inserted_at::date
            order by inserted_at desc
        ) as rn
    from {{ ref('stg_cmc__quotes') }}

),

quotes_daily as (

    select * from quotes where rn = 1

)

select
    l.inserted_at::date                     as snapshot_date,
    l.coin_id,
    coalesce(d.coin_name, q.coin_name)      as coin_name,
    coalesce(d.coin_symbol, q.coin_symbol)  as coin_symbol,
    l.cmc_rank,
    -- First appearance: lag() has no prior row -> coalesce to the coin's own
    -- rank so prev_cmc_rank is never null and rank_change is 0, not null.
    -- New entrants stay identifiable via is_new_entry (the old
    -- `prev_cmc_rank is null` filter semantics live there now).
    coalesce(
        lag(l.cmc_rank) over (
            partition by l.coin_id
            order by l.inserted_at::date
        ),
        l.cmc_rank
    )                                       as prev_cmc_rank,
    
        lag(l.cmc_rank) over (
            partition by l.coin_id
            order by l.inserted_at::date
        ) - l.cmc_rank,
        
                                          as rank_change,
    lag(l.cmc_rank) over (
        partition by l.coin_id
        order by l.inserted_at::date
    ) is null                               as is_new_entry,
    lag(l.inserted_at::date) over (
        partition by l.coin_id
        order by l.inserted_at::date
    )                                       as prev_snapshot_date,
    q.price,
    q.market_cap,
    q.volume_24h,
    q.percent_change_24h,
    l.date_added_at
from listings_daily l
left join quotes_daily q
    on q.coin_id = l.coin_id
   and q.inserted_at::date = l.inserted_at::date
left join {{ ref('dim_coins') }} d
    on d.coin_id = l.coin_id
