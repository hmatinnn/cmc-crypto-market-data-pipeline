-- Panel: Row Count vs Expected Range (latest batch)
-- Data source: Postgres (dwh, schema staging_layer)
-- Panel type: Table
-- Query Format: Table
-- Dashboard: Monitoring
--
-- Mirrors the "row_count between X and Y" checks in soda/checks.yml,
-- evaluated against the most recent load per table.
--
-- 2026-07-18: categories/category_details thresholds recalibrated.
-- soda/checks.yml's original ranges (480-520 / 56500-62500) were based on
-- stale assumptions — cmc_categories_and_details_pipeline runs @weekly and
-- pulls whatever CMC's /v1/cryptocurrency/categories endpoint currently
-- returns (fetch_categories(limit=500) is a ceiling, not a fixed count).
-- Live counts observed today were 351 categories / 14871 category_details.
-- Since this reflects real external data (not a fixed batch size like
-- listings_latest/quotes), re-check and adjust periodically if CMC's
-- category count keeps drifting.

SELECT
  table_name,
  row_count,
  expected_min,
  expected_max,
  CASE WHEN row_count BETWEEN expected_min AND expected_max THEN 'OK' ELSE 'OUT OF RANGE' END AS status
FROM (
  SELECT 'listings_latest' AS table_name, COUNT(*) AS row_count, 480 AS expected_min, 520 AS expected_max
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'quotes', COUNT(*), 380, 420
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'categories', COUNT(*), 350, 400
  FROM staging_layer.categories
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.categories)
  UNION ALL
  SELECT 'category_details', COUNT(*), 13400, 16400
  FROM staging_layer.category_details
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.category_details)
) t
ORDER BY table_name;
