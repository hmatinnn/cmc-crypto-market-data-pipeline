from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime
import os

CSV_BASE_PATH = "/opt/airflow/api_responses_csv"


TABLES = {
    "listings_latest": {
        "columns": [
            "id", "infinite_supply", "circulating_supply", "total_supply",
            "max_supply", "date_added", "num_market_pairs", "cmc_rank",
            "last_updated", "tvl_ratio", "self_reported_circulating_supply",
            "self_reported_market_cap", "minted_market_cap", "inserted_at"
        ],
        # "pk": ["id", "inserted_at"],  
        "csv_file": "listing_latest.csv",
    },

    "categories": {
        "columns": [
            "id", "name", "title", "description", "volume", "num_tokens",
            "avg_price_change", "market_cap", "market_cap_change",
            "volume_change", "last_updated", "inserted_at"
        ],
        # "pk": ["id", "inserted_at"],
        "csv_file": "categories.csv",
    },

    "category_details": {
        "columns": [
            "id", "name", "title", "description", "volume", "num_tokens",
            "last_updated", "avg_price_change", "market_cap",
            "market_cap_change", "volume_change", "coins_id", "inserted_at"
        ],
        # "pk": ["id", "coins_id", "inserted_at"],
        "csv_file": "category_details.csv",
    },

    "map": {
        "columns": [
            "id", "name", "symbol", "slug", "is_active",
            "first_historical_data", "last_historical_data"
        ],
        # "pk": ["id"],
        "csv_file": "map.csv",
    },

    "info": {
        "columns": [
            "id", "category", "description", "logo",
            "date_launched"
        ],
        # "pk": ["id"],
        "csv_file": "info.csv",
    },

    "quotes": {
        "columns": [
            "id", "name", "symbol", "slug", "is_fiat", "quote_id",
            "quote_symbol", "quote_price", "quote_volume_24h",
            "quote_volume_change_24h", "quote_cex_volume_24h",
            "quote_dex_volume_24h", "quote_percent_change_1h",
            "quote_percent_change_24h", "quote_percent_change_7d",
            "quote_percent_change_30d", "quote_percent_change_60d",
            "quote_percent_change_90d", "quote_market_cap",
            "quote_market_cap_dominance", "quote_fully_diluted_market_cap",
            "quote_minted_market_cap", "quote_tvl", "quote_last_updated", "inserted_at"
        ],
        # "pk": ["id", "quote_id", "inserted_at"],
        "csv_file": "quotes.csv",
    },
}


def load_table(table_key, **context):
  
    cfg = TABLES[table_key]
    csv_path = os.path.join(CSV_BASE_PATH, cfg["csv_file"])

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found at {csv_path}")

    pg_hook = PostgresHook(postgres_conn_id="postgres_dwh")
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    table_name = f"staging_layer.{table_key}"
    tmp_table = f"tmp_{table_key}"
    columns = cfg["columns"]

    cur.execute(f"""
        CREATE TEMP TABLE {tmp_table} AS
        SELECT * FROM {table_name} WITH NO DATA;
    """)

    with open(csv_path, "r") as f:
        cur.copy_expert(
            f"""
            COPY {tmp_table} ({", ".join(columns)})
            FROM STDIN WITH CSV HEADER
            """,
            f,
        )

    cur.execute(f"TRUNCATE TABLE {table_name};")
    cur.execute(f"""
        INSERT INTO {table_name}
        SELECT * FROM {tmp_table};
    """)

    conn.commit()
    cur.close()
    conn.close()


with DAG(
    dag_id="load_staging_tables_dag",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["staging", "load"],
) as dag:

    for table_key in TABLES:
        PythonOperator(
            task_id=f"load_{table_key}_data",
            python_callable=load_table,
            op_kwargs={"table_key": table_key},
        )