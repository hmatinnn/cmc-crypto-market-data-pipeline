-- Panel: Data Quality — Missing Value % (latest batch, ALL soda checks.yml columns)
-- Data source: Postgres (dwh, schema staging_layer)
-- Panel type: Table
-- Query Format: Table
-- Dashboard: Monitoring
--
-- Full 1:1 mirror of every missing_count()/missing_percent() check in
-- soda/checks.yml across categories, category_details, info,
-- listings_latest, and quotes (map has no checks defined in checks.yml).
-- missing_count(x) = 0 checks are expressed here as threshold_percent = 0.
-- info has no inserted_at column (not a historical/batched table), so it
-- is checked against its full current contents, no batch filter.
-- 45 checks total.

SELECT table_name, column_name, missing_percent, threshold_percent,
       CASE WHEN missing_percent > threshold_percent THEN 'FAIL' ELSE 'OK' END AS status
FROM (
  SELECT 'categories' AS table_name, 'id' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE id IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.categories
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.categories)
  UNION ALL
  SELECT 'categories' AS table_name, 'market_cap_change' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE market_cap_change IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         15 AS threshold_percent
  FROM staging_layer.categories
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.categories)
  UNION ALL
  SELECT 'category_details' AS table_name, 'id' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE id IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.category_details
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.category_details)
  UNION ALL
  SELECT 'category_details' AS table_name, 'coins_id' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE coins_id IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.category_details
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.category_details)
  UNION ALL
  SELECT 'category_details' AS table_name, 'market_cap_change' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE market_cap_change IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         15 AS threshold_percent
  FROM staging_layer.category_details
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.category_details)
  UNION ALL
  SELECT 'info' AS table_name, 'date_launched' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE date_launched IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         15 AS threshold_percent
  FROM staging_layer.info
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'id' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE id IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'cmc_rank' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE cmc_rank IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'last_updated' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE last_updated IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'date_added' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE date_added IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'num_market_pairs' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE num_market_pairs IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'circulating_supply' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE circulating_supply IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'total_supply' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE total_supply IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'infinite_supply' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE infinite_supply IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'minted_market_cap' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE minted_market_cap IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'inserted_at' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE inserted_at IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'max_supply' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE max_supply IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         50 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'tvl_ratio' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE tvl_ratio IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         96 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'self_reported_circulating_supply' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE self_reported_circulating_supply IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         45 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'listings_latest' AS table_name, 'self_reported_market_cap' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE self_reported_market_cap IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         45 AS threshold_percent
  FROM staging_layer.listings_latest
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.listings_latest)
  UNION ALL
  SELECT 'quotes' AS table_name, 'id' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE id IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'name' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE name IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'symbol' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE symbol IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'slug' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE slug IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'is_fiat' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE is_fiat IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_id' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_id IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_symbol' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_symbol IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_volume_24h' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_volume_24h IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_volume_change_24h' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_volume_change_24h IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_cex_volume_24h' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_cex_volume_24h IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_dex_volume_24h' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_dex_volume_24h IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_percent_change_1h' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_percent_change_1h IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_percent_change_24h' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_percent_change_24h IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_percent_change_7d' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_percent_change_7d IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_percent_change_30d' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_percent_change_30d IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_percent_change_60d' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_percent_change_60d IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_percent_change_90d' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_percent_change_90d IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_market_cap_dominance' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_market_cap_dominance IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_fully_diluted_market_cap' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_fully_diluted_market_cap IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_minted_market_cap' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_minted_market_cap IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_last_updated' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_last_updated IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'inserted_at' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE inserted_at IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         0 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_price' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_price IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         1 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_market_cap' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_market_cap IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         1 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
  UNION ALL
  SELECT 'quotes' AS table_name, 'quote_tvl' AS column_name,
         ROUND(100.0 * COUNT(*) FILTER (WHERE quote_tvl IS NULL) / NULLIF(COUNT(*), 0), 2) AS missing_percent,
         96 AS threshold_percent
  FROM staging_layer.quotes
  WHERE inserted_at = (SELECT MAX(inserted_at) FROM staging_layer.quotes)
) t
ORDER BY table_name, column_name;
