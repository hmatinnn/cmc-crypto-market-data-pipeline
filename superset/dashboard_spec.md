# CMC Crypto Analytics — Superset Dashboard Spesifikasiyası

Bir dashboard, 4 tab. Bütün chartlar dbt-nin `analytics` schema-sındakı view-lara oturur
(`vw_market_overview_daily`, `vw_coin_explorer`, `vw_sector_performance`, `vw_coin_momentum_daily`).

**Data mənbəyi qaydası:** cari vəziyyət → `olap` əsaslı view-lar (`vw_coin_explorer`,
`vw_sector_performance`); tarixi trend → staging əsaslı view-lar (`vw_market_overview_daily`,
`vw_coin_momentum_daily`).

**Aqreqat qeydi:** `vw_coin_explorer` (1 sətir/coin) və `vw_sector_performance`
(1 sətir/kateqoriya) onsuz da aqreqatlıdır — Superset metrik tələb edəndə `MAX(...)`
yaz, nəticəni dəyişmir, sadəcə sintaksis tələbidir.

---

## Tab 1 — Market Overview

**Dataset:** `analytics.vw_market_overview_daily` (grain: 1 sətir / gün)

| Chart | Superset tipi | X-Axis | Metrics | Dimensions |
|---|---|---|---|---|
| Total Market Cap | Big Number w/ Trendline | Time column: `snapshot_date` | `MAX(total_market_cap)` | — |
| 24h Volume | Big Number w/ Trendline | `snapshot_date` | `MAX(total_volume_24h)` | — |
| BTC Dominance | Big Number w/ Trendline | `snapshot_date` | `MAX(btc_dominance_pct)` | — |
| Top-10 Share | Big Number w/ Trendline | `snapshot_date` | `MAX(top10_market_cap_share)` (% format) | — |
| Market Cap trendi | Line Chart | `snapshot_date` | `MAX(total_market_cap)` | — |
| BTC Dom. vs Top-10 | Mixed Time-series | `snapshot_date` | Query A: `MAX(btc_dominance_pct)`, Query B: `MAX(top10_market_cap_share)` | — |
| CEX vs DEX həcm | Area Chart (stacked) | `snapshot_date` | `MAX(total_cex_volume_24h)`, `MAX(total_dex_volume_24h)` | — |
| DEX payı trendi | Line Chart | `snapshot_date` | `MAX(dex_volume_share)` | — |

---

## Tab 2 — Coin Explorer

**Dataset:** `analytics.vw_coin_explorer` (grain: 1 sətir / coin)
**Filter:** dashboard filter — `coin_symbol`, cross-filtering aktiv.

### Top-100 cədvəl — Table
- Query Mode: **Raw Records** (metrik lazım deyil)
- Columns: `cmc_rank`, `coin_symbol`, `coin_name`, `price`, `percent_change_1h`,
  `percent_change_24h`, `percent_change_7d`, `percent_change_30d`, `market_cap`, `volume_24h`
- Sort: `cmc_rank` ASC, Row limit: 100
- Customize → Conditional Formatting: bütün `percent_change_*` sütunlarına qırmızı-yaşıl

### MC vs Volume — Bubble Chart
(Supersetdə scatter üçün doğru tip **Bubble Chart**-dır: x və y hər ikisi metrikdir)
- Entity: `coin_symbol`
- X Axis: `MAX(market_cap)`
- Y Axis: `MAX(volume_24h)`
- Bubble Size: `MAX(market_cap)`
- Series: — (boş saxla)
- Customize: hər iki ox **Log Scale**
- Row limit: 500

### FDV/MC Top-20 — Bar Chart (horizontal)
- X-Axis (dimension): `coin_symbol`
- Metrics: `MAX(fdv_mc_ratio)`
- Filters: `market_cap > 100000000` (kiçik coinlərdə səs-küy)
- Sort by: metrik DESC, Row limit: 20

### Supply Utilization — Bar Chart
- X-Axis: `coin_symbol`
- Metrics: `MAX(supply_utilization)`
- Filters: `is_infinite_supply = false`, `max_supply IS NOT NULL`
- Sort by: metrik DESC (və ya ASC — hansı ucu göstərmək istəyirsənsə), Row limit: 20

### MC/TVL (DeFi) — Table
- Query Mode: Raw Records
- Columns: `coin_symbol`, `coin_name`, `tvl`, `market_cap`, `mc_tvl_ratio`
- Filters: `tvl IS NOT NULL`
- Sort: `mc_tvl_ratio` ASC (aşağı nisbət = TVL-ə görə "ucuz"), Row limit: 50

---

## Tab 3 — Sectors

**Dataset:** `analytics.vw_sector_performance` (grain: 1 sətir / kateqoriya)

### Sektor xəritəsi — Treemap
- Dimensions: `category_name`
- Metric (size): `MAX(market_cap)`
- Row limit: 50

### Narrativ performansı 7d — Bar Chart (horizontal)
- X-Axis (dimension): `category_name`
- Metrics: `MAX(avg_change_7d_pct)`
- Sort by: metrik DESC, Row limit: 20
- Customize: müsbət/mənfi bar rəngi (positive/negative color)

### Narrativ performansı 30d — Bar Chart
- Eyni konfiq, Metrics: `MAX(avg_change_30d_pct)`

### Sektor həcmi — Bar Chart
- X-Axis: `category_name`
- Metrics: `MAX(volume_24h)`
- Sort by: metrik DESC, Row limit: 15

### Sektor detalları — Table
- Query Mode: Raw Records
- Columns: `category_name`, `num_coins`, `market_cap`, `avg_change_24h_pct`, `mc_tvl_ratio`
- Sort: `market_cap` DESC

---

## Tab 4 — Momentum

**Dataset:** `analytics.vw_coin_momentum_daily` (grain: 1 sətir / coin / gün)

"Son gün" cədvəlləri üçün əvvəlcə **virtual dataset** yarat
(Superset → Datasets → + Dataset → SQL):

```sql
select *
from analytics.vw_coin_momentum_daily
where snapshot_date = (select max(snapshot_date) from analytics.vw_coin_momentum_daily)
```

Adı: `vw_coin_momentum_latest`. Aşağıdakı 3 cədvəl bu virtual dataset-dən oxuyur.

### Rank Gainers — Table (`vw_coin_momentum_latest`)
- Query Mode: Raw Records
- Columns: `coin_symbol`, `coin_name`, `cmc_rank`, `prev_cmc_rank`, `rank_change`
- Filters: `rank_change IS NOT NULL`
- Sort: `rank_change` DESC, Row limit: 20

### Rank Losers — Table (`vw_coin_momentum_latest`)
- Eyni konfiq, Sort: `rank_change` ASC

### Top-500-ə yeni girənlər — Table (`vw_coin_momentum_latest`)
- Columns: `coin_symbol`, `coin_name`, `cmc_rank`, `market_cap`, `date_added_at`
- Filters: `is_new_entry = true` (prev_cmc_rank artıq null olmur — ilk görünüşdə
  öz rankına coalesce olunur, rank_change = 0)
- Sort: `cmc_rank` ASC

### Coinin rank tarixi — Line Chart (`vw_coin_momentum_daily`)
- X-Axis: `snapshot_date`
- Metrics: custom SQL metric → `-MIN(cmc_rank)` (mənfi işarə y-oxu "tərs çevirmək"
  üçündür — Superset line chart-da invert-y yoxdur; rank 1 qrafikin yuxarısında görünür)
- Dimensions (series): `coin_symbol`
- Dashboard-un coin filtrinə bağlıdır — filtrsiz 500 xətt çəkməsin deyə
  chart-a default filtr qoy (məs. `cmc_rank <= 10`)

### Volatillik Top-20 — Bar Chart (`vw_coin_momentum_daily`)
- X-Axis (dimension): `coin_symbol`
- Metrics: custom SQL metric → `STDDEV(percent_change_24h)`
- Sort by: metrik DESC, Row limit: 20
- Qeyd: bütün günlər üzərindən hesablanır, time range filtrinə bağlama

### Yeni coinlərin performansı — Table (`analytics.vw_coin_explorer`)
- Query Mode: Raw Records
- Columns: `coin_symbol`, `coin_name`, `date_added_at`, `percent_change_30d`,
  `market_cap`, `cmc_rank`
- Filters: `is_new_coin_90d = true`
- Sort: `percent_change_30d` DESC

---

## Ümumi qurulum qeydləri

1. **Time Range filtri:** dashboard səviyyəsində `snapshot_date`-ə bağlı vahid filtr —
   yalnız Tab 1 və Tab 4-ün time-series chartlarına scope et.
2. **Table chartlarda** həmişə Raw Records rejimi — aqreqat lazım deyil, view-lar
   onsuz da düzgün grain-dədir.
3. **Rəng standartı:** bütün percent_change metriklərində eyni qırmızı-yaşıl şkala.
4. **Cache:** data gündə bir dəfə yeniləndiyi üçün dataset cache timeout ~1 saat kifayətdir.
5. **Aqreqatlı view-larda** (`vw_coin_explorer`, `vw_sector_performance`) `MAX(...)`
   sadəcə Superset-in metrik sintaksis tələbidir — grain 1 sətir olduğu üçün dəyəri dəyişmir.
