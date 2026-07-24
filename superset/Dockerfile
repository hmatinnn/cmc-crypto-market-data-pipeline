FROM apache/superset:latest

USER root
# Superset runs from its own virtualenv at /app/.venv, managed by uv --
# there's no pip binary inside it at all (confirmed via
# `docker run --entrypoint bash apache/superset:latest -c "ls /app/.venv/bin"`).
# Install straight into that venv with uv instead.
RUN uv pip install --python /app/.venv/bin/python psycopg2-binary
USER superset
