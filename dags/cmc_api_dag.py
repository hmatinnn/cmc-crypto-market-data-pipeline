from airflow.decorators import dag, task
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime
import sys

sys.path.append("/opt/airflow/jobs")

from telegram_alert import send_dag_failure_alert

from cmc_api_pull import (
    fetch_map,
    fetch_listings,
    fetch_categories,
    fetch_category_details,
    fetch_info,
    fetch_quotes,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "on_failure_callback": send_dag_failure_alert,
}


TRIGGER_POKE_INTERVAL = 15


@dag(
    schedule="@daily",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def cmc_daily_listings_quotes_fetch_pipeline():

   
    t_listings = task(fetch_listings)()
    t_quotes = task(fetch_quotes)()

    trigger_parse = TriggerDagRunOperator(
        task_id="trigger_cmc_daily_listings_quotes_parse_pipeline",
        trigger_dag_id="cmc_daily_listings_quotes_parse_pipeline",
        wait_for_completion=True,
        poke_interval=TRIGGER_POKE_INTERVAL,
    )

    t_listings >> t_quotes >> trigger_parse


@dag(
    schedule="@monthly",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def cmc_monthly_map_info_fetch_pipeline():

    
    t_map = task(fetch_map)()
    t_info = task(fetch_info)()

    trigger_parse = TriggerDagRunOperator(
        task_id="trigger_cmc_monthly_map_info_parse_pipeline",
        trigger_dag_id="cmc_monthly_map_info_parse_pipeline",
        wait_for_completion=True,
        poke_interval=TRIGGER_POKE_INTERVAL,
    )

    t_map >> t_info >> trigger_parse


@dag(

   
    schedule="0 0 * * 1",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def cmc_weekly_categories_fetch_pipeline():
    t_cat = task(fetch_categories)()
    t_details = task(fetch_category_details)()

    trigger_parse = TriggerDagRunOperator(
        task_id="trigger_cmc_weekly_categories_parse_pipeline",
        trigger_dag_id="cmc_weekly_categories_parse_pipeline",
        wait_for_completion=True,
        poke_interval=TRIGGER_POKE_INTERVAL,
    )

    t_cat >> t_details >> trigger_parse


cmc_daily_listings_quotes_fetch_pipeline()
cmc_monthly_map_info_fetch_pipeline()
cmc_weekly_categories_fetch_pipeline()
