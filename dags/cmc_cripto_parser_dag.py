from airflow.decorators import dag, task
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
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

    # load_staging_tables_dag reads the CSVs this task just wrote. It used to
    # run on its own separate @daily schedule, which raced with this task's
    # write and occasionally COPY'd a half-written file (BadCopyFileFormat:
    # missing data for column ...). Trigger it explicitly instead, so it can
    # only ever start after the CSVs are fully flushed to disk.
    trigger_staging_load = TriggerDagRunOperator(
        task_id="trigger_load_staging_tables_dag",
        trigger_dag_id="load_staging_tables_dag",
        wait_for_completion=False,
    )

    parse_bronze_to_silver() >> trigger_staging_load


cmc_silver_parser_pipeline()