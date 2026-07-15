from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime

CREATE_LISTINGS_LATEST_SQL = """
CREATE TABLE IF NOT EXISTS staging_layer.listings_latest (
    id                                  BIGINT,
    infinite_supply                     BOOLEAN,
    circulating_supply                  NUMERIC(30, 4),
    total_supply                        NUMERIC(30, 4),
    max_supply                          NUMERIC(30, 4),
    date_added                          TIMESTAMP,
    num_market_pairs                    INTEGER,
    cmc_rank                            INTEGER,
    last_updated                        TIMESTAMP,
    tvl_ratio                           NUMERIC(20, 6),
    self_reported_circulating_supply    NUMERIC(30, 4),
    self_reported_market_cap            NUMERIC(30, 4),
    minted_market_cap                   NUMERIC(30, 4),
    inserted_at                         TIMESTAMP
   
);
"""


CREATE_CATEGORIES_SQL = """
CREATE TABLE IF NOT EXISTS staging_layer.categories (
    id                  VARCHAR(50),
    name                VARCHAR(100),
    title               VARCHAR(150),
    description         TEXT,
    volume              NUMERIC(30, 4),
    num_tokens          INTEGER,
    avg_price_change    NUMERIC(20, 6),
    market_cap          NUMERIC(30, 4),
    market_cap_change   NUMERIC(20, 6),
    volume_change       NUMERIC(20, 6),
    last_updated        TIMESTAMP,
    inserted_at                         TIMESTAMP
    
);
"""

CREATE_CATEGORY_DETAILS_SQL = """
CREATE TABLE IF NOT EXISTS staging_layer.category_details (
    id                  VARCHAR(50),
    name                VARCHAR(100),
    title               VARCHAR(150),
    description         TEXT,
    volume              NUMERIC(30, 4),
    num_tokens          INTEGER,
    last_updated        TIMESTAMP,
    avg_price_change    NUMERIC(20, 6),
    market_cap          NUMERIC(30, 4),
    market_cap_change   NUMERIC(20, 6),
    volume_change       NUMERIC(20, 6),
    coins_id            BIGINT,
    inserted_at                         TIMESTAMP
);
"""

CREATE_MAP_SQL = """
CREATE TABLE IF NOT EXISTS staging_layer.map (
    id                      BIGINT,
    name                    VARCHAR(100),
    symbol                  VARCHAR(20),
    slug                    VARCHAR(100),
    is_active               SMALLINT,
    first_historical_data   TIMESTAMP,
    last_historical_data    TIMESTAMP
);
"""

CREATE_INFO_SQL = """
CREATE TABLE IF NOT EXISTS staging_layer.info (
    id              BIGINT,
    category        VARCHAR(100),
    description     TEXT,
    logo            VARCHAR(255),
    date_launched   TIMESTAMP
);
"""

CREATE_QUOTES_SQL = """
CREATE TABLE IF NOT EXISTS staging_layer.quotes (
    id                              BIGINT,
    name                            VARCHAR(100),
    symbol                          VARCHAR(20),
    slug                            VARCHAR(100),
    is_fiat                         SMALLINT,
    quote_id                        BIGINT,
    quote_symbol                    VARCHAR(20),
    quote_price                     NUMERIC(30, 10),
    quote_volume_24h                NUMERIC(30, 4),
    quote_volume_change_24h         NUMERIC(20, 6),
    quote_cex_volume_24h            NUMERIC(30, 4),
    quote_dex_volume_24h            NUMERIC(30, 4),
    quote_percent_change_1h         NUMERIC(20, 6),
    quote_percent_change_24h        NUMERIC(20, 6),
    quote_percent_change_7d         NUMERIC(20, 6),
    quote_percent_change_30d        NUMERIC(20, 6),
    quote_percent_change_60d        NUMERIC(20, 6),
    quote_percent_change_90d        NUMERIC(20, 6),
    quote_market_cap                NUMERIC(30, 4),
    quote_market_cap_dominance      NUMERIC(20, 6),
    quote_fully_diluted_market_cap  NUMERIC(30, 4),
    quote_minted_market_cap         NUMERIC(30, 4),
    quote_tvl                       NUMERIC(30, 4),
    quote_last_updated              TIMESTAMP,
    inserted_at                     TIMESTAMP
);
"""


def create_listings_latest_table(**context):
    pg_hook = PostgresHook(postgres_conn_id="postgres_dwh")
    conn = pg_hook.get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_LISTINGS_LATEST_SQL)
    conn.commit()
    cur.close()
    conn.close()


def create_categories_table(**context):
    pg_hook = PostgresHook(postgres_conn_id="postgres_dwh")
    conn = pg_hook.get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_CATEGORIES_SQL)
    conn.commit()
    cur.close()
    conn.close()


def create_category_details_table(**context):
    pg_hook = PostgresHook(postgres_conn_id="postgres_dwh")
    conn = pg_hook.get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_CATEGORY_DETAILS_SQL)
    conn.commit()
    cur.close()
    conn.close()

def create_info_table(**context):
    pg_hook = PostgresHook(postgres_conn_id="postgres_dwh")
    conn = pg_hook.get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_INFO_SQL)
    conn.commit()
    cur.close()
    conn.close()

def create_map_table(**context):
    pg_hook = PostgresHook(postgres_conn_id="postgres_dwh")
    conn = pg_hook.get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_MAP_SQL)
    conn.commit()
    cur.close()
    conn.close()


def create_quotes_table(**context):
    pg_hook = PostgresHook(postgres_conn_id="postgres_dwh")
    conn = pg_hook.get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_QUOTES_SQL)
    conn.commit()
    cur.close()
    conn.close()
    


with DAG(
    dag_id="create_staging_tables_dag",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["staging", "setup"],
) as dag:

    create_listings_latest_task = PythonOperator(
        task_id="create_listings_latest_table",
        python_callable=create_listings_latest_table,
    )

    create_categories_task = PythonOperator(
        task_id="create_categories_table",
        python_callable=create_categories_table,
    )

    create_category_details_task = PythonOperator(
        task_id="create_category_details_table",
        python_callable=create_category_details_table,
    )

    create_map_task = PythonOperator(
        task_id="create_map_table",
        python_callable=create_map_table,
    )

    create_info_task = PythonOperator(
        task_id="create_info_table",
        python_callable=create_info_table,
    )

    create_quotes_task = PythonOperator(
        task_id="create_quotes_table",
        python_callable=create_quotes_table,
    )

    [
        create_listings_latest_task,
        create_categories_task,
        create_category_details_task,
        create_map_task,
        create_info_task,
        create_quotes_task,
    ]
