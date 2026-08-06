#!/usr/bin/env bash
#
# Deploy script executed on the server. GitHub Actions (cd.yml) invokes it over
# SSH, but it can also be run manually:
#
#   cd /opt/coinmarket_pipeline_project && ./deploy/deploy.sh main
#
# The .env file must be created MANUALLY on the server - it is not in the repo.

set -euo pipefail

BRANCH="${1:-main}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "Deploy started | branch=$BRANCH | dir=$PROJECT_DIR"

# --- 1. Pre-flight checks ---------------------------------------------------
if [ ! -f .env ]; then
  echo "ERROR: .env file is missing. Copy it from .env.example and fill it in." >&2
  exit 1
fi

command -v docker >/dev/null || { echo "ERROR: docker not found" >&2; exit 1; }
docker compose version >/dev/null || { echo "ERROR: 'docker compose' plugin is missing" >&2; exit 1; }

# Windows -> Linux guard #1: a .env copied from Windows carries CRLF endings.
# docker compose would then read values with a trailing \r (e.g. an API key
# becomes "abc123\r" and every request fails with 401).
if grep -qU $'\r' .env 2>/dev/null; then
  log "WARNING: .env has CRLF line endings - converting to LF."
  sed -i 's/\r$//' .env
fi

# Windows -> Linux guard #2: on Linux, bind-mounted volumes need AIRFLOW_UID to
# match the host user, otherwise logs/ and dags/ end up owned by root and the
# scheduler fails with "Permission denied". On Windows this variable is ignored,
# so it is often left empty.
CURRENT_UID="$(id -u)"
if ! grep -qE "^AIRFLOW_UID=[0-9]+$" .env; then
  log "AIRFLOW_UID is not set correctly - setting it to $CURRENT_UID"
  sed -i '/^AIRFLOW_UID=/d' .env
  echo "AIRFLOW_UID=$CURRENT_UID" >> .env
elif [ "$(grep -E '^AIRFLOW_UID=' .env | cut -d= -f2)" != "$CURRENT_UID" ]; then
  log "WARNING: AIRFLOW_UID in .env does not match the current user ($CURRENT_UID)."
  log "         If you hit permission errors, update it."
fi

# --- 2. Update the code -----------------------------------------------------
PREV_SHA="$(git rev-parse HEAD)"
log "Current commit: $PREV_SHA"

git fetch --prune origin
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"

NEW_SHA="$(git rev-parse HEAD)"
log "New commit: $NEW_SHA"

if [ "$PREV_SHA" = "$NEW_SHA" ]; then
  log "No changes, but images will still be rebuilt (idempotent)."
fi

# --- 3. Build images --------------------------------------------------------
log "Building images..."
docker compose build --pull

# --- 4. Bring services up ---------------------------------------------------
# The DB migration is handled by the airflow-init service, which has
# _AIRFLOW_DB_MIGRATE=true and runs automatically as part of "up".
# (Do not call "docker compose run airflow-cli" here - that service sits behind
# the "debug" profile and is not available by default.)
log "Updating services..."
docker compose up -d --remove-orphans

log "Waiting for airflow-init to finish (DB migration)..."
docker compose wait airflow-init 2>/dev/null || true

# --- 5. Health check --------------------------------------------------------
log "Waiting 30s for services to come up..."
sleep 30

if docker compose ps --format '{{.Name}} {{.State}}' | grep -qiE 'exited|restarting'; then
  log "WARNING: some containers are unhealthy:"
  docker compose ps
  log "To roll back: git reset --hard $PREV_SHA && ./deploy/deploy.sh"
  exit 1
fi

log "All services are running:"
docker compose ps

# --- 6. Cleanup -------------------------------------------------------------
log "Pruning old images..."
docker image prune -f

log "Deploy completed successfully | $NEW_SHA"
