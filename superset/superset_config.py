import os

# Used to sign cookies/session data. Override via SUPERSET_SECRET_KEY in .env
# for anything beyond local dev.
SECRET_KEY = os.environ.get(
    "SUPERSET_SECRET_KEY", "please_change_this_secret_key_in_env"
)

# Superset's OWN metadata (dashboards, charts, users, saved connections) --
# lives in the dedicated superset-db service, NOT in the cmc "dwh" warehouse.
# The dwh connection (olap/staging_layer schemas) is added separately, from
# the Superset UI, after first login: Settings -> Database Connections ->
# + Database -> PostgreSQL -> host "postgres", port 5432, database "dwh".
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://superset:superset@superset-db:5432/superset"

REDIS_HOST = "redis"
REDIS_PORT = 6379

# Reuses the same Redis instance Airflow's Celery broker uses (db 0) --
# separate logical DB index so the two never collide.
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": 3,
}
DATA_CACHE_CONFIG = CACHE_CONFIG
FILTER_STATE_CACHE_CONFIG = CACHE_CONFIG
EXPLORE_FORM_DATA_CACHE_CONFIG = CACHE_CONFIG
