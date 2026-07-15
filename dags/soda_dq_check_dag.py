from airflow.decorators import dag, task
from datetime import datetime
import sys

sys.path.append("/opt/airflow/jobs")

from soda_scan import run_soda_scan
from telegram_alert import send_dag_failure_alert

default_args = {
    "owner": "airflow",
    "retries": 0,
    "on_failure_callback": send_dag_failure_alert,
}

@dag(
    schedule="@daily",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc", "dq"],
    default_args=default_args,
    on_failure_callback=send_dag_failure_alert,
)
def soda_dq_check_pipeline():
    task(run_soda_scan)()

soda_dq_check_pipeline()