# CMC Crypto Analytics — Superset Dashboard Specification

One dashboard, 4 tabs. All charts sit on top of the views in dbt's `analytics` schema
(`vw_market_overview_daily`, `vw_coin_explorer`, `vw_sector_performance`, `vw_coin_momentum_daily`).

**Data source rule:** current state → `olap`-based views (`vw_coin_explorer`,
`vw_sector_performance`); historical trend → staging-based views (`vw_market_overview_daily`,
`vw_coin_momentum_daily`).

**Note on aggregation:** `vw_coin_explorer` (1 row/coin) and `vw_sector_performance`
(1 row/category) are already aggregated — when Superset requires a metric, write `MAX(...)`.
It does not change the result, it is only a syntax requirement.

---

## Tab 1 — Market Overview

**Dataset:** `analytics.vw_market_overview_daily` (grain: 1 row / day)

| Chart | Superset type | X-Axis | Metrics | Dimensions |
|---|---|---|---|---|
| Total Market Cap | Big Number w/ Trendline | Time column: `snapshot_date` | `MAX(total_market_cap)` | — |
| 24h Volume | Big Number w/ Trendline | `snapshot_date` | `MAX(total_volume_24h)` | — |
| BTC Dominance | Big Number w/ Trendline | `snapshot_date` | `MAX(btc_dominance_pct)` | — |
| Top-10 Share | Big Number w/ Trendline | `snapshot_date` | `MAX(top10_market_cap_share)` (% format) | — |
| Market Cap trend | Line Chart | `snapshot_date` | `MAX(total_market_cap)` | — |
| BTC Dom. vs Top-10 | Mixed Time-series | `snapshot_date` | Query A: `MAX(btc_dominance_pct)`, Query B: `MAX(top10_market_cap_share)` | — |
| CEX vs DEX volume | Area Chart (stacked) | `snapshot_date` | `MAX(total_cex_volume_24h)`, `MAX(total_dex_volume_24h)` | — |
| DEX share trend | Line Chart | `snapshot_date` | `MAX(dex_volume_share)` | — |

---

## Tab 2 — Coin Explorer

**Dataset:** `analytics.vw_coin_explorer` (grain: 1 row / coin)
**Filter:** dashboard filter — `coin_symbol`, cross-filtering enabled.

### Top-100 table — Table
- Query Mode: **Raw Records** (no metric needed)
- Columns: `cmc_rank`, `coin_symbol`, `coin_name`, `price`, `percent_change_1h`,
  `percent_change_24h`, `percent_change_7d`, `percent_change_30d`, `market_cap`, `volume_24h`
- Sort: `cmc_rank` ASC, Row limit: 100
- Customize → Conditional Formatting: red-green scale on all `percent_change_*` columns

### MC vs Volume — Bubble Chart
(In Superset the correct type for a scatter plot is **Bubble Chart**: both x and y are metrics)
- Entity: `coin_symbol`
- X Axis: `MAX(market_cap)`
- Y Axis: `MAX(volume_24h)`
- Bubble Size: `MAX(market_cap)`
- Series: — (leave empty)
- Customize: **Log Scale** on both axes
- Row limit: 500

### FDV/MC Top-20 — Bar Chart (horizontal)
- X-Axis (dimension): `coin_symbol`
- Metrics: `MAX(fdv_mc_ratio)`
- Filters: `market_cap > 100000000` (small coins are noisy)
- Sort by: metric DESC, Row limit: 20

### Supply Utilization — Bar Chart
- X-Axis: `coin_symbol`
- Metrics: `MAX(supply_utilization)`
- Filters: `is_infinite_supply = false`, `max_supply IS NOT NULL`
- Sort by: metric DESC (or ASC — whichever end you want to show), Row limit: 20

### MC/TVL (DeFi) — Table
- Query Mode: Raw Records
- Columns: `coin_symbol`, `coin_name`, `tvl`, `market_cap`, `mc_tvl_ratio`
- Filters: `tvl IS NOT NULL`
- Sort: `mc_tvl_ratio` ASC (lower ratio = "cheap" relative to TVL), Row limit: 50

---

## Tab 3 — Sectors

**Dataset:** `analytics.vw_sector_performance` (grain: 1 row / category)

### Sector map — Treemap
- Dimensions: `category_name`
- Metric (size): `MAX(market_cap)`
- Row limit: 50

### Narrative performance 7d — Bar Chart (horizontal)
- X-Axis (dimension): `category_name`
- Metrics: `MAX(avg_change_7d_pct)`
- Sort by: metric DESC, Row limit: 20
- Customize: positive/negative bar colors

### Narrative performance 30d — Bar Chart
- Same config, Metrics: `MAX(avg_change_30d_pct)`

### Sector volume — Bar Chart
- X-Axis: `category_name`
- Metrics: `MAX(volume_24h)`
- Sort by: metric DESC, Row limit: 15

### Sector details — Table
- Query Mode: Raw Records
- Columns: `category_name`, `num_coins`, `market_cap`, `avg_change_24h_pct`, `mc_tvl_ratio`
- Sort: `market_cap` DESC

---

## Tab 4 — Momentum

**Dataset:** `analytics.vw_coin_momentum_daily` (grain: 1 row / coin / day)

For the "latest day" tables, first create a **virtual dataset**
(Superset → Datasets → + Dataset → SQL):

```sql
select *
from analytics.vw_coin_momentum_daily
where snapshot_date = (select max(snapshot_date) from analytics.vw_coin_momentum_daily)
```

Name it `vw_coin_momentum_latest`. The 3 tables below read from this virtual dataset.

### Rank Gainers — Table (`vw_coin_momentum_latest`)
- Query Mode: Raw Records
- Columns: `coin_symbol`, `coin_name`, `cmc_rank`, `prev_cmc_rank`, `rank_change`
- Filters: `rank_change IS NOT NULL`
- Sort: `rank_change` DESC, Row limit: 20

### Rank Losers — Table (`vw_coin_momentum_latest`)
- Same config, Sort: `rank_change` ASC

### New entries into the Top-500 — Table (`vw_coin_momentum_latest`)
- Columns: `coin_symbol`, `coin_name`, `cmc_rank`, `market_cap`, `date_added_at`
- Filters: `is_new_entry = true` (prev_cmc_rank is no longer null — on first appearance
  it is coalesced to its own rank, rank_change = 0)
- Sort: `cmc_rank` ASC

### Rank history of a coin — Line Chart (`vw_coin_momentum_daily`)
- X-Axis: `snapshot_date`
- Metrics: custom SQL metric → `-MIN(cmc_rank)` (the negative sign is there to "invert"
  the y-axis — Superset line charts have no invert-y; rank 1 then appears at the top of the chart)
- Dimensions (series): `coin_symbol`
- Tied to the dashboard's coin filter — add a default filter on the chart
  (e.g. `cmc_rank <= 10`) so it does not draw 500 lines when unfiltered

### Volatility Top-20 — Bar Chart (`vw_coin_momentum_daily`)
- X-Axis (dimension): `coin_symbol`
- Metrics: custom SQL metric → `STDDEV(percent_change_24h)`
- Sort by: metric DESC, Row limit: 20
- Note: computed across all days, do not bind it to the time range filter

### Performance of new coins — Table (`analytics.vw_coin_explorer`)
- Query Mode: Raw Records
- Columns: `coin_symbol`, `coin_name`, `date_added_at`, `percent_change_30d`,
  `market_cap`, `cmc_rank`
- Filters: `is_new_coin_90d = true`
- Sort: `percent_change_30d` DESC

---

## General setup notes

1. **Time Range filter:** a single dashboard-level filter bound to `snapshot_date` —
   scope it only to the time-series charts of Tab 1 and Tab 4.
2. **In Table charts** always use Raw Records mode — no aggregation is needed, the views
   are already at the correct grain.
3. **Color standard:** the same red-green scale on all percent_change metrics.
4. **Cache:** since the data refreshes once a day, a dataset cache timeout of ~1 hour is enough.
5. **In aggregated views** (`vw_coin_explorer`, `vw_sector_performance`) `MAX(...)` is
   purely Superset's metric syntax requirement — with a grain of 1 row it does not change the value.
