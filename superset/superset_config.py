import os


SECRET_KEY = os.environ.get(
    "SUPERSET_SECRET_KEY", "please_change_this_secret_key_in_env"
)


SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://superset:superset@superset-db:5432/superset"

REDIS_HOST = "redis"
REDIS_PORT = 6379


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
