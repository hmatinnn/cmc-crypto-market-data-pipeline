-- Panel: Duplicate Key Check (latest batch)
-- Data source: Postgres (dwh, schema staging_layer)
-- Panel type: Table
-- Query Format: Table
-- Dashboard: Monitoring
--
-- Mirrors the "failed rows" uniqueness checks in soda/checks.yml
-- (id/id+quote_id/id+coins_id + inserted_at should be unique).

SELECT table_name, duplicate_groups,
       CASE WHEN duplicate_groups = 0 THEN 'OK' ELSE 'FAIL' END AS status
FROM (
  SELECT 'listings_latest' AS table_name, COUNT(*) AS duplicate_groups FROM (
    SELECT id, inserted_at FROM staging_layer.listings_latest
    WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
    GROUP BY id, inserted_at HAVING COUNT(*) > 1
  ) d
  UNION ALL
  SELECT 'quotes', COUNT(*) FROM (
    SELECT id, quote_id, inserted_at FROM staging_layer.quotes
    WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
    GROUP BY id, quote_id, inserted_at HAVING COUNT(*) > 1
  ) d
  UNION ALL
  SELECT 'categories', COUNT(*) FROM (
    SELECT id, inserted_at FROM staging_layer.categories
    WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.categories)
    GROUP BY id, inserted_at HAVING COUNT(*) > 1
  ) d
  UNION ALL
  SELECT 'category_details', COUNT(*) FROM (
    SELECT id, coins_id, inserted_at FROM staging_layer.category_details
    WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.category_details)
    GROUP BY id, coins_id, inserted_at HAVING COUNT(*) > 1
  ) d
) t
ORDER BY table_name;
