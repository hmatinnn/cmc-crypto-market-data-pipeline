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




@dag(
    dag_id="dbt_daily_fact_coin_market_pipeline",
    schedule=None,
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["dbt", "cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def dbt_daily_fact_coin_market_pipeline():

    task(run_dbt, pool="dbt_shared_pool")(select="cmc_pipeline", target_path="target_daily")


@dag(
    dag_id="dbt_weekly_dim_categories_pipeline",
    schedule=None,
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["dbt", "cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def dbt_weekly_dim_categories_pipeline():

  
    task(run_dbt, pool="dbt_shared_pool")(select="cmc_pipeline", target_path="target_weekly")


@dag(
    dag_id="dbt_monthly_dim_coins_pipeline",
    schedule=None,
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["dbt", "cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def dbt_monthly_dim_coins_pipeline():

 
    task(run_dbt, pool="dbt_shared_pool")(select="cmc_pipeline", target_path="target_monthly")


dbt_daily_fact_coin_market_pipeline()
dbt_weekly_dim_categories_pipeline()
dbt_monthly_dim_coins_pipeline()
