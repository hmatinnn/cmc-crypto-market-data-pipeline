from airflow.decorators import dag, task
from datetime import datetime
import sys

sys.path.append("/opt/airflow/jobs")

from telegram_alert import send_dag_failure_alert
from dbt_runner import run_dbt

default_args = {
    "owner": "airflow",
    "retries": 1,
    "on_failure_callback": send_dag_failure_alert,
}


# Keeps the dbt-built Postgres tables (staging_layer / intermediate_layer /
# olap schemas) fresh for direct consumption by Superset (or any other tool
# querying Postgres) -- no Google Sheets step involved.
#
# Cadence mirrors cmc_api_dag.py's own source-fetch schedules, so each dbt
# run only fires once its upstream raw data could actually have changed:
#   - listings_latest / quotes -> @daily  (cmc_listings_pipeline)
#   - categories / category_details -> @weekly (cmc_categories_and_details_pipeline)
#   - map / info -> @monthly (cmc_map_pipeline / cmc_info_pipeline)

@dag(
    dag_id="dbt_daily_pipeline",
    schedule="@daily",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["dbt", "cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def dbt_daily_pipeline():
    # `+fact_coin_market` pulls in every upstream ancestor (stg_cmc__listings_latest,
    # stg_cmc__quotes, stg_cmc__map, stg_cmc__info, int_coins, int_coin_market_snapshot).
    task(run_dbt)(select="+fact_coin_market", target_path="target_daily")


@dag(
    dag_id="dbt_weekly_pipeline",
    schedule="@weekly",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["dbt", "cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def dbt_weekly_pipeline():
    # `+` on both pulls in stg_cmc__categories, stg_cmc__category_details,
    # stg_cmc__map, stg_cmc__info, int_coins, int_category_snapshot, and
    # int_category_coin_bridge.
    task(run_dbt)(select="+dim_categories +bridge_category_coin", target_path="target_weekly")


@dag(
    dag_id="dbt_monthly_pipeline",
    schedule="@monthly",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["dbt", "cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def dbt_monthly_pipeline():
    # `+dim_coins` pulls in stg_cmc__map, stg_cmc__info, int_coins.
    task(run_dbt)(select="+dim_coins", target_path="target_monthly")


dbt_daily_pipeline()
dbt_weekly_pipeline()
dbt_monthly_pipeline()
