from airflow.decorators import dag, task
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


@dag(
    schedule="@daily",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def cmc_listings_pipeline():
    # fetch_quotes now derives its data from fetch_listings's own response
    # (see cmc_api_pull.py) instead of a separate API call, so it must run
    # right after fetch_listings in the same DAG run -- as its own
    # separately-scheduled DAG it could read a stale/missing listings file.
    t_listings = task(fetch_listings)()
    t_quotes = task(fetch_quotes)()
    t_listings >> t_quotes


@dag(
    schedule="@monthly",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def cmc_map_pipeline():
    task(fetch_map)()


@dag(
    schedule="@monthly",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def cmc_info_pipeline():
    task(fetch_info)()


@dag(
    schedule="@weekly",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def cmc_categories_and_details_pipeline():
    t_cat = task(fetch_categories)()
    t_details = task(fetch_category_details)()
    t_cat >> t_details


cmc_listings_pipeline()
cmc_map_pipeline()
cmc_info_pipeline()
cmc_categories_and_details_pipeline()