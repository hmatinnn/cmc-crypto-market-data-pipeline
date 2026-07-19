-- Panel: Table Freshness
-- Data source: Postgres (dwh, schema staging_layer)
-- Panel type: Table
-- Query Format: Table
-- Dashboard: Pipeline — Freshness & Volume

SELECT 'listings_latest' AS table_name, MAX(inserted_at) AS last_inserted
FROM staging_layer.listings_latest
UNION ALL
SELECT 'quotes', MAX(inserted_at) FROM staging_layer.quotes
UNION ALL
SELECT 'categories', MAX(inserted_at) FROM staging_layer.categories
UNION ALL
SELECT 'category_details', MAX(inserted_at) FROM staging_layer.category_details
;
