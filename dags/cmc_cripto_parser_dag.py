from airflow.decorators import dag, task
from datetime import datetime
import sys

sys.path.append("/opt/airflow/jobs")

from cmc_json_parse_to_csv import main as run_crypto_parser


@dag(
    schedule="@daily",
    start_date=datetime(2026, 7, 2),
    catchup=False,
    tags=["cmc", "silver"],
)
def cmc_silver_parser_pipeline():
    @task
    def parse_bronze_to_silver():
        result = run_crypto_parser()
        print(f"Parsed datasets: {result}")
        return result

    parse_bronze_to_silver()


cmc_silver_parser_pipeline()