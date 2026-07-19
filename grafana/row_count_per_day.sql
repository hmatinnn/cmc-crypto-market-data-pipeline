-- Panel: Row Count per Load (per day, per table)
-- Data source: Postgres (dwh, schema staging_layer)
-- Panel type: Bar chart
-- Query Format: Table
-- Dashboard: Pipeline — Freshness & Volume
--
-- Note: map and info tables have no inserted_at column, so they are
-- excluded here. If a freshness/volume equivalent column is added to
-- those tables later, add them back the same way as the other four.

SELECT
  day,
  SUM(CASE WHEN metric = 'listings_latest' THEN value END) AS listings_latest,
  SUM(CASE WHEN metric = 'quotes' THEN value END) AS quotes,
  SUM(CASE WHEN metric = 'categories' THEN value END) AS categories,
  SUM(CASE WHEN metric = 'category_details' THEN value END) AS category_details
FROM (
  SELECT date_trunc('day', inserted_at) AS day, 'listings_latest' AS metric, COUNT(*) AS value
  FROM staging_layer.listings_latest WHERE $__timeFilter(inserted_at) GROUP BY 1
  UNION ALL
  SELECT date_trunc('day', inserted_at), 'quotes', COUNT(*)
  FROM staging_layer.quotes WHERE $__timeFilter(inserted_at) GROUP BY 1
  UNION ALL
  SELECT date_trunc('day', inserted_at), 'categories', COUNT(*)
  FROM staging_layer.categories WHERE $__timeFilter(inserted_at) GROUP BY 1
  UNION ALL
  SELECT date_trunc('day', inserted_at), 'category_details', COUNT(*)
  FROM staging_layer.category_details WHERE $__timeFilter(inserted_at) GROUP BY 1
) t
GROUP BY day
ORDER BY day;
