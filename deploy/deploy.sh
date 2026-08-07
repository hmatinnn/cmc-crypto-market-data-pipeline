#!/usr/bin/env bash
#
# Deploy script executed on the server. GitHub Actions (cd.yml) invokes it over
# SSH, but it can also be run manually:
#
#   cd /opt/coinmarket_pipeline_project && ./deploy/deploy.sh main
#
# The .env file must be created MANUALLY on the server - it is not in the repo.

set -euo pipefail

# Step 2 below runs "git reset --hard", which rewrites THIS FILE while it is
# still executing. Bash reads a script lazily by byte offset, so replacing the
# file underneath a running shell can make it resume at the wrong position and
# execute garbage. Re-exec from a private copy first, so the running code is
# immune to the checkout.
if [ "${DEPLOY_SELF_COPY:-0}" != "1" ]; then
  DEPLOY_PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  export DEPLOY_PROJECT_DIR
  SELF_COPY="$(mktemp)"
  cp "${BASH_SOURCE[0]}" "$SELF_COPY"
  export DEPLOY_SELF_COPY=1 DEPLOY_SELF_COPY_PATH="$SELF_COPY"
  exec bash "$SELF_COPY" "$@"
fi

# Clean up the temporary copy of this script when we are done with it.
trap 'rm -f "${DEPLOY_SELF_COPY_PATH:-}"' EXIT

BRANCH="${1:-main}"
PROJECT_DIR="${DEPLOY_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
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

# Five services (grafana, superset, superset-db, superset-init, dbt) pin an
# explicit container_name. Those names are GLOBAL in Docker - they are not
# namespaced by compose project - so when a service is recreated the old
# container can still hold the name and "up" fails with:
#
#   Conflict. The container name "/grafana" is already in use by container ...
#
# Normal path: a plain "up" with no downtime. If a name conflict does happen,
# free only the names Docker actually complained about and try once more.
UP_LOG="$(mktemp)"
trap 'rm -f "$UP_LOG" "${DEPLOY_SELF_COPY_PATH:-}"' EXIT

# Docker aborts on the FIRST name it cannot claim, so one conflict is reported
# per attempt. With five pinned container_names that means up to five rounds -
# hence a loop rather than a single retry.
MAX_UP_ATTEMPTS=8
attempt=1

while : ; do
  if docker compose up -d --remove-orphans 2>&1 | tee "$UP_LOG"; then
    break
  fi

  CONFLICTS="$(grep -oE 'The container name "/[^"]+"' "$UP_LOG" \
               | sed -E 's|.*"/([^"]+)".*|\1|' | sort -u)"

  if [ -z "$CONFLICTS" ]; then
    log "ERROR: 'docker compose up' failed for a reason other than a name conflict."
    exit 1
  fi

  if [ "$attempt" -ge "$MAX_UP_ATTEMPTS" ]; then
    log "ERROR: still hitting name conflicts after $MAX_UP_ATTEMPTS attempts."
    log "Inspect manually with: docker ps -a"
    exit 1
  fi

  log "Name conflict (attempt $attempt/$MAX_UP_ATTEMPTS): $(echo "$CONFLICTS" | tr '\n' ' ')"

  # A partially completed "up" leaves a mixed state: some containers attached to
  # the old compose network, some to the new one. Postgres then keeps running
  # while airflow-init cannot resolve the hostname "postgres" at all.
  #
  # So tear the project down completely - containers AND network - instead of
  # picking off containers one by one. Named volumes are preserved; "down"
  # only removes them when called with -v.
  log "Tearing the project down to rebuild a consistent network..."
  docker compose down --remove-orphans || true

  # Containers left over from an older compose project keep their pinned names
  # and survive "down", so remove those explicitly.
  for name in $CONFLICTS; do
    docker rm -f "$name" >/dev/null 2>&1 || true
  done

  attempt=$((attempt + 1))
done

log "Waiting for airflow-init to finish (DB migration)..."
INIT_RC=0
docker compose wait airflow-init >/dev/null 2>&1 || INIT_RC=$?
if [ "$INIT_RC" -ne 0 ]; then
  log "WARNING: airflow-init exited with code $INIT_RC. Logs:"
  docker compose logs --tail 40 airflow-init || true
fi

# --- 5. Health check --------------------------------------------------------
log "Waiting 45s for services to come up..."
sleep 45

# airflow-init and superset-init are one-shot containers: they do their work and
# exit with code 0. That is healthy, so they must not be treated as failures.
# Anything else that exited non-zero, or is stuck restarting, is a real problem.
UNHEALTHY="$(docker compose ps --all --format json 2>/dev/null | python3 -c '
import json, sys

ONE_SHOT = {"airflow-init", "superset-init"}
raw = sys.stdin.read().strip()
if not raw:
    sys.exit(0)

# Compose emits either a JSON array or newline-delimited JSON objects
# depending on the version - handle both.
try:
    rows = json.loads(raw)
    if isinstance(rows, dict):
        rows = [rows]
except json.JSONDecodeError:
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]

for r in rows:
    service = r.get("Service") or r.get("Name", "")
    state = (r.get("State") or "").lower()
    code = r.get("ExitCode", 0)
    if state == "restarting":
        print(f"{service}: stuck restarting")
    elif state == "exited":
        if service in ONE_SHOT and code == 0:
            continue          # expected
        print(f"{service}: exited with code {code}")
')"

if [ -n "$UNHEALTHY" ]; then
  log "WARNING: some containers are unhealthy:"
  echo "$UNHEALTHY"
  echo
  docker compose ps --all
  log "To roll back: git reset --hard $PREV_SHA && bash deploy/deploy.sh"
  exit 1
fi

log "All services are healthy:"
docker compose ps

# --- 6. Cleanup -------------------------------------------------------------
log "Pruning old images..."
docker image prune -f

log "Deploy completed successfully | $NEW_SHA"
