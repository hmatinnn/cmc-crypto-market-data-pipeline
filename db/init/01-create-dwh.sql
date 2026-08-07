-- Creates the data warehouse database.
--
-- The Postgres image runs every .sql file in /docker-entrypoint-initdb.d/ once,
-- the first time the data volume is initialised. POSTGRES_DB only creates the
-- Airflow metadata database ("airflow"), so without this file a fresh clone
-- would have nowhere to land the warehouse and every DAG would fail with
-- "database dwh does not exist".
--
-- Schemas inside dwh are created by the create_schemas_dag.

SELECT 'CREATE DATABASE dwh'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dwh')\gexec
