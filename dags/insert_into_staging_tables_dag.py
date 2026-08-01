from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime
import sys

sys.path.append("/opt/airflow/jobs")

from load_staging_tables import GROUPS, load_table
from telegram_alert import send_dag_failure_alert

default_args = {
    "owner": "airflow",
    "retries": 1,
    "on_failure_callback": send_dag_failure_alert,
}



TRIGGER_POKE_INTERVAL = 15

DBT_DAG_ID = {
    "daily": "dbt_daily_fact_coin_market_pipeline",
    "weekly": "dbt_weekly_dim_categories_pipeline",
    "monthly": "dbt_monthly_dim_coins_pipeline",
}


def _make_load_dag(dag_id: str, group: str) -> DAG:
    dbt_dag_id = DBT_DAG_ID[group]

    with DAG(
        dag_id=dag_id,
        start_date=datetime(2026, 1, 1),
        schedule=None,
        catchup=False,
        tags=["staging", "load", group],
        default_args=default_args,
        on_failure_callback=send_dag_failure_alert,
    ) as dag:
        trigger_dbt = TriggerDagRunOperator(
            task_id=f"trigger_{dbt_dag_id}",
            trigger_dag_id=dbt_dag_id,
            wait_for_completion=True,
            poke_interval=TRIGGER_POKE_INTERVAL,
        )

        for table_key in GROUPS[group]:
            load_task = PythonOperator(
                task_id=f"load_{table_key}_data",
                python_callable=load_table,
                op_kwargs={"table_key": table_key},
            )
            load_task >> trigger_dbt

    return dag


cmc_daily_listings_quotes_load_pipeline = _make_load_dag(
    "cmc_daily_listings_quotes_load_pipeline", "daily"
)
cmc_weekly_categories_load_pipeline = _make_load_dag(
    "cmc_weekly_categories_load_pipeline", "weekly"
)
cmc_monthly_map_info_load_pipeline = _make_load_dag(
    "cmc_monthly_map_info_load_pipeline", "monthly"
)
