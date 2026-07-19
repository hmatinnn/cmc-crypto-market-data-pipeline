-- Panel: Table Freshness with SLA (per-table thresholds)
-- Data source: Postgres (dwh, schema staging_layer)
-- Panel type: Table
-- Query Format: Table
-- Dashboard: Monitoring
--
-- Mirrors the freshness() checks in soda/checks.yml, with one correction:
--   categories        <= 8 days (192h) -- corrected: soda/checks.yml says
--                                          1d, but cmc_categories_and_details_pipeline
--                                          runs @weekly, so a 24h SLA would
--                                          false-alarm STALE almost every day.
--                                          192h = 7-day cadence + 1 day buffer.
--   listings_latest   <= 2 days (48h)
--   quotes             <= 2 days (48h)
--   category_details  <= 9 days (216h)

SELECT
  table_name,
  last_inserted,
  ROUND(EXTRACT(EPOCH FROM (NOW() - last_inserted)) / 3600, 1) AS hours_since_update,
  sla_hours,
  CASE WHEN NOW() - last_inserted > make_interval(hours => sla_hours) THEN 'STALE' ELSE 'OK' END AS status
FROM (
  SELECT 'listings_latest' AS table_name, MAX(inserted_at) AS last_inserted, 48 AS sla_hours FROM staging_layer.listings_latest
  UNION ALL
  SELECT 'quotes', MAX(inserted_at), 48 FROM staging_layer.quotes
  UNION ALL
  SELECT 'categories', MAX(inserted_at), 192 FROM staging_layer.categories
  UNION ALL
  SELECT 'category_details', MAX(inserted_at), 216 FROM staging_layer.category_details
) t
ORDER BY table_name;
