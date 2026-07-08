from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime

def create_schemas(**context):
    pg_hook = PostgresHook(postgres_conn_id="postgres_dwh")
    conn = pg_hook.get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE SCHEMA IF NOT EXISTS staging_layer;
        CREATE SCHEMA IF NOT EXISTS intermediate_layer;
        CREATE SCHEMA IF NOT EXISTS olap;
    """)
    conn.commit()
    cur.close()
    conn.close()

with DAG(
    dag_id="create_schemas_dag",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["setup"],
) as dag:

    create_schemas_task = PythonOperator(
        task_id="create_schemas",
        python_callable=create_schemas,
    )