#!/usr/bin/env bash
#
# Creates the server-side .env file.
#
#   cd /opt/coinmarket_pipeline_project
#   bash deploy/init-env.sh
#
# Generated automatically:
#   AIRFLOW_UID          - taken from the current user
#   FERNET_KEY           - 32 random bytes, urlsafe-base64
#   POSTGRES_PASSWORD    - 32 random characters
#   GF_ADMIN_PASSWORD    - 24 random characters
#   SUPERSET_ADMIN_PASSWORD - 24 random characters
#
# Asked interactively (only you have these):
#   X_CMC_PRO_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
#
# The script never prints secrets to the terminal and never sends them anywhere.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

ENV_FILE=".env"
EXAMPLE_FILE=".env.example"

bold() { echo -e "\033[1m$*\033[0m"; }
warn() { echo -e "\033[1;33m[!]\033[0m $*"; }

[ -f "$EXAMPLE_FILE" ] || { echo "$EXAMPLE_FILE not found - wrong directory?" >&2; exit 1; }

if [ -f "$ENV_FILE" ]; then
  warn "$ENV_FILE already exists."
  read -r -p "Overwrite it? A backup will be kept. (y/N): " answer
  [[ "$answer" =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 0; }
  cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"
fi

cp "$EXAMPLE_FILE" "$ENV_FILE"
sed -i 's/\r$//' "$ENV_FILE"   # in case the example file carries CRLF

# --- helpers ----------------------------------------------------------------

# Writes KEY=value, replacing the existing line if present.
set_var() {
  local key="$1" val="$2"
  if grep -qE "^${key}=" "$ENV_FILE"; then
    # Use a delimiter unlikely to appear in the value.
    python3 - "$ENV_FILE" "$key" "$val" <<'PY'
import sys, re
path, key, val = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(path, encoding="utf-8").read()
src = re.sub(rf"^{re.escape(key)}=.*$", f"{key}={val}", src, count=1, flags=re.MULTILINE)
open(path, "w", encoding="utf-8").write(src)
PY
  else
    echo "${key}=${val}" >> "$ENV_FILE"
  fi
}

# A Fernet key is urlsafe-base64 of 32 random bytes.
gen_fernet() { openssl rand -base64 32 | tr '+/' '-_'; }
gen_pass()   { openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c "${1:-32}"; }

# --- generated values -------------------------------------------------------

bold "Generating values..."

set_var AIRFLOW_UID "$(id -u)"
set_var FERNET_KEY "$(gen_fernet)"
set_var POSTGRES_PASSWORD "$(gen_pass 32)"
set_var GF_ADMIN_PASSWORD "$(gen_pass 24)"
set_var SUPERSET_ADMIN_PASSWORD "$(gen_pass 24)"

echo "  AIRFLOW_UID             = $(id -u)"
echo "  FERNET_KEY              = (generated)"
echo "  POSTGRES_PASSWORD       = (generated)"
echo "  GF_ADMIN_PASSWORD       = (generated)"
echo "  SUPERSET_ADMIN_PASSWORD = (generated)"

# --- interactive values -----------------------------------------------------

echo
bold "Now enter the values only you have."
echo "(input is hidden; press Enter to leave a value empty)"
echo

read -r -s -p "  CoinMarketCap API key : " cmc_key;   echo
read -r -s -p "  Telegram bot token    : " tg_token;  echo
read -r    -p "  Telegram chat id      : " tg_chat

[ -n "$cmc_key" ] && set_var X_CMC_PRO_API_KEY "$cmc_key"
[ -n "$tg_token" ] && set_var TELEGRAM_BOT_TOKEN "$tg_token"
[ -n "$tg_chat" ] && set_var TELEGRAM_CHAT_ID "$tg_chat"

# --- finish -----------------------------------------------------------------

chmod 600 "$ENV_FILE"
sed -i 's/\r$//' "$ENV_FILE"

echo
bold "Done. $ENV_FILE created (permissions 600)."
echo
echo "Empty values left to fill in by hand (if any):"
grep -nE "^[A-Z_]+=$" "$ENV_FILE" || echo "  none - every variable has a value"

echo
echo "To see the admin passwords later:"
echo "  grep -E 'GF_ADMIN_PASSWORD|SUPERSET_ADMIN_PASSWORD' $ENV_FILE"
echo
echo "Next step:  bash deploy/deploy.sh dev"
