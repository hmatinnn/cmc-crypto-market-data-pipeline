from airflow.decorators import dag, task
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime
import sys

sys.path.append("/opt/airflow/jobs")

from cmc_json_parse_to_csv import main as run_crypto_parser
from telegram_alert import send_dag_failure_alert

default_args = {
    "owner": "airflow",
    "retries": 1,
    "on_failure_callback": send_dag_failure_alert,
}


TRIGGER_POKE_INTERVAL = 15


def _make_parse_dag(dag_id: str, group: str, load_dag_id: str):
    @dag(
        dag_id=dag_id,
        start_date=datetime(2026, 7, 2),
        schedule=None,
        catchup=False,
        tags=["cmc", "silver", group],
        default_args=default_args,
        on_failure_callback=send_dag_failure_alert,
    )
    def _pipeline():
        @task
        def parse_bronze_to_silver():
            result = run_crypto_parser(group=group)
            print(f"Parsed datasets ({group}): {result}")
            return result

        trigger_load = TriggerDagRunOperator(
            task_id=f"trigger_{load_dag_id}",
            trigger_dag_id=load_dag_id,
            wait_for_completion=True,
            poke_interval=TRIGGER_POKE_INTERVAL,
        )

        parse_bronze_to_silver() >> trigger_load

    return _pipeline()


cmc_daily_listings_quotes_parse_pipeline = _make_parse_dag(
    "cmc_daily_listings_quotes_parse_pipeline",
    "daily",
    "cmc_daily_listings_quotes_load_pipeline",
)
cmc_weekly_categories_parse_pipeline = _make_parse_dag(
    "cmc_weekly_categories_parse_pipeline",
    "weekly",
    "cmc_weekly_categories_load_pipeline",
)
cmc_monthly_map_info_parse_pipeline = _make_parse_dag(
    "cmc_monthly_map_info_parse_pipeline",
    "monthly",
    "cmc_monthly_map_info_load_pipeline",
)
