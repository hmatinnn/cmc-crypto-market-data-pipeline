-- Panel: Airflow DAG Run Status (latest run per DAG)
-- Data source: Postgres — REQUIRES A NEW Grafana data source pointing at
--   the "airflow" database (same Postgres host/container, different DB,
--   e.g. host=postgres, port=5432, database=airflow, user/pass=airflow).
--   The existing "grafana-postgresql-datasource-1" points at "dwh" and
--   cannot see these tables.
-- Panel type: Table
-- Query Format: Table
-- Dashboard: Monitoring

SELECT
  dr.dag_id,
  dr.state,
  dr.start_date,
  dr.end_date,
  ROUND(EXTRACT(EPOCH FROM (dr.end_date - dr.start_date)) / 60, 1) AS duration_minutes
FROM dag_run dr
INNER JOIN (
  SELECT dag_id, MAX(start_date) AS max_start
  FROM dag_run
  GROUP BY dag_id
) latest ON latest.dag_id = dr.dag_id AND latest.max_start = dr.start_date
ORDER BY dr.dag_id;

-- Companion panel — DAG success rate over the selected time range:
--
-- SELECT
--   dag_id,
--   COUNT(*) AS total_runs,
--   ROUND(100.0 * COUNT(*) FILTER (WHERE state = 'success') / COUNT(*), 1) AS success_rate_pct
-- FROM dag_run
-- WHERE $__timeFilter(start_date)
-- GROUP BY dag_id
-- ORDER BY dag_id;
