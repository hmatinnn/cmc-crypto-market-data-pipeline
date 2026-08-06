#!/usr/bin/env bash
#
# One-time server preparation. Run as root on a fresh Ubuntu VPS:
#
#   bash server-setup.sh
#
# What it does:
#   1. creates a non-root "deploy" user and adds it to the docker group
#   2. adds a 4GB swap file (this stack needs ~5GB and the box has 7.8GB)
#   3. creates /opt/coinmarket_pipeline_project owned by deploy
#   4. prepares ~/.ssh for the GitHub Actions key
#
# The script is idempotent - running it twice is safe.
# It never handles private keys or passwords; you add those yourself.

set -euo pipefail

DEPLOY_USER="deploy"
PROJECT_DIR="/opt/coinmarket_pipeline_project"
SWAP_FILE="/swapfile"
SWAP_SIZE_GB=4

log() { echo -e "\n\033[1;32m==>\033[0m $*"; }
warn() { echo -e "\033[1;33m[!]\033[0m $*"; }

[ "$(id -u)" -eq 0 ] || { echo "This script must be run as root." >&2; exit 1; }

# --- 1. Deploy user ---------------------------------------------------------
log "1/4  Deploy user: $DEPLOY_USER"

if id "$DEPLOY_USER" &>/dev/null; then
  echo "     user already exists - skipping"
else
  adduser --disabled-password --gecos "" "$DEPLOY_USER"
  echo "     created"
fi

# Password login stays disabled: this account is reachable by SSH key only.
if getent group docker >/dev/null; then
  usermod -aG docker "$DEPLOY_USER"
  echo "     added to the docker group"
else
  warn "docker group not found - is Docker installed?"
fi

DEPLOY_UID="$(id -u "$DEPLOY_USER")"
echo "     uid = $DEPLOY_UID   (this is the AIRFLOW_UID value for .env)"

# --- 2. Swap ----------------------------------------------------------------
log "2/4  Swap file (${SWAP_SIZE_GB}GB)"

if swapon --show | grep -q "$SWAP_FILE"; then
  echo "     swap is already active - skipping"
else
  if [ -f "$SWAP_FILE" ]; then
    warn "$SWAP_FILE exists but is not active - reusing it"
  else
    fallocate -l "${SWAP_SIZE_GB}G" "$SWAP_FILE" || \
      dd if=/dev/zero of="$SWAP_FILE" bs=1M count=$((SWAP_SIZE_GB * 1024))
  fi
  chmod 600 "$SWAP_FILE"
  mkswap "$SWAP_FILE"
  swapon "$SWAP_FILE"
  echo "     activated"
fi

# Persist across reboots.
if ! grep -q "^${SWAP_FILE}" /etc/fstab; then
  echo "$SWAP_FILE none swap sw 0 0" >> /etc/fstab
  echo "     added to /etc/fstab"
fi

# Containers should only swap under real pressure, not eagerly.
if ! grep -q "^vm.swappiness" /etc/sysctl.conf; then
  echo "vm.swappiness=10" >> /etc/sysctl.conf
  sysctl -q vm.swappiness=10
  echo "     vm.swappiness set to 10"
fi

# --- 3. Project directory ---------------------------------------------------
log "3/4  Project directory: $PROJECT_DIR"

mkdir -p "$PROJECT_DIR"
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$PROJECT_DIR"
echo "     ready and owned by $DEPLOY_USER"

# --- 4. SSH directory -------------------------------------------------------
log "4/4  SSH directory for $DEPLOY_USER"

DEPLOY_HOME="$(getent passwd "$DEPLOY_USER" | cut -d: -f6)"
install -d -m 700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "$DEPLOY_HOME/.ssh"
touch "$DEPLOY_HOME/.ssh/authorized_keys"
chmod 600 "$DEPLOY_HOME/.ssh/authorized_keys"
chown "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_HOME/.ssh/authorized_keys"
echo "     $DEPLOY_HOME/.ssh/authorized_keys is ready"

# --- Summary ----------------------------------------------------------------
cat <<EOF

==========================================================================
 DONE. Current state:

   deploy user : $DEPLOY_USER  (uid $DEPLOY_UID)
   project dir : $PROJECT_DIR
   swap        : $(swapon --show=NAME,SIZE --noheadings | tr '\n' ' ')
   memory      : $(free -h | awk '/Mem:/{print $2" total, "$7" available"}')

 NEXT STEPS (see CI_CD.md section 4):

   1. Add the GitHub Actions PUBLIC key to:
        $DEPLOY_HOME/.ssh/authorized_keys

   2. Clone the repository as the deploy user:
        su - $DEPLOY_USER
        git clone <REPO_URL> $PROJECT_DIR

   3. Create the .env file on the server (do NOT copy it from Windows):
        cd $PROJECT_DIR
        cp .env.example .env
        nano .env
      Set AIRFLOW_UID=$DEPLOY_UID

   4. Run the first deploy manually:
        bash deploy/deploy.sh main
==========================================================================
EOF
