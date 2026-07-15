from soda.scan import Scan
from airflow.providers.postgres.hooks.postgres import PostgresHook
import sys

sys.path.append("/opt/airflow/jobs")
from telegram_alert import send_soda_alert

SODA_DIR = "/opt/airflow/soda"
POSTGRES_CONN_ID = "postgres_dwh"


def build_configuration_yaml(conn_id: str) -> str:
    hook = PostgresHook(postgres_conn_id=conn_id)
    conn = hook.get_connection(conn_id)

    return f"""
data_source postgres:
  type: postgres
  host: {conn.host}
  port: {conn.port or 5432}
  username: {conn.login}
  password: {conn.password}
  database: {conn.schema}
"""


def run_soda_scan():
    scan = Scan()
    scan.set_data_source_name("postgres")

    config_yaml = build_configuration_yaml(POSTGRES_CONN_ID)
    scan.add_configuration_yaml_str(config_yaml)
    scan.add_sodacl_yaml_file(file_path=f"{SODA_DIR}/checks.yml")

    scan.execute()

    print(scan.get_logs_text())

    send_soda_alert(scan)

    # if scan.has_check_fails():
    #     raise Exception("Soda data quality checks failed. See logs for details.")


if __name__ == "__main__":
    run_soda_scan()