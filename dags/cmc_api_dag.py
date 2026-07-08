from airflow.decorators import dag, task
from datetime import datetime
import sys

sys.path.append("/opt/airflow/jobs")

from cmc_api_pull import (
    fetch_map,
    fetch_listings,
    fetch_categories,
    fetch_category_details,
    fetch_info,
    fetch_quotes,
)


@dag(
    schedule="@daily",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc"],
)

def cmc_listings_pipeline():
    task(fetch_listings)()


@dag(
    schedule="@daily",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc"],
)
def cmc_quotes_pipeline():
    task(fetch_quotes)()


@dag(
    schedule="@weekly",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc"],
)
def cmc_map_pipeline():
    task(fetch_map)()


@dag(
    schedule="@weekly",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc"],
)
def cmc_info_pipeline():
    task(fetch_info)()


@dag(
    schedule="@monthly",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc"],
)
def cmc_categories_and_details_pipeline():
    t_cat = task(fetch_categories)()
    t_details = task(fetch_category_details)()
    t_cat >> t_details


cmc_listings_pipeline()
cmc_quotes_pipeline()
cmc_map_pipeline()
cmc_info_pipeline()
cmc_categories_and_details_pipeline()