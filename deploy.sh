#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

UPGRADE_REMOTE_DEPS="${UPGRADE_REMOTE_DEPS:-0}"
SKIP_DASHBOARD_BUILD="${SKIP_DASHBOARD_BUILD:-0}"
SKIP_DASHBOARD_INSTALL="${SKIP_DASHBOARD_INSTALL:-0}"
SKIP_REMOTE_DEPS="${SKIP_REMOTE_DEPS:-0}"

for arg in "$@"; do
  case "$arg" in
    --upgrade|-u)
      UPGRADE_REMOTE_DEPS=1
      ;;
    --skip-deps)
      SKIP_REMOTE_DEPS=1
      SKIP_DASHBOARD_INSTALL=1
      ;;
    --skip-dashboard)
      SKIP_DASHBOARD_BUILD=1
      ;;
    --help|-h)
      echo "Usage: ./deploy.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --upgrade, -u         Upgrade remote Python dependencies to latest"
      echo "  --skip-deps           Skip installing/updating dashboard and remote Python dependencies"
      echo "  --skip-dashboard      Skip building the React dashboard"
      echo "  --help, -h            Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg"
      echo "Run './deploy.sh --help' for usage."
      exit 1
      ;;
  esac
done

required_vars=(PI_USER PI_HOST PI_APP_DIR PI_SERVICE_NAME)
for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    echo "Missing required environment variable: ${var}"
    echo "Example: PI_USER=pi PI_HOST=raspberrypi.local PI_APP_DIR=/opt/wavedisp PI_SERVICE_NAME=wavedisp ./deploy.sh"
    exit 1
  fi
done

if [ ! -f wavedisp.service ]; then
  echo "Error: wavedisp.service not found."
  echo "Please copy wavedisp.service.example to wavedisp.service and update it with your paths."
  exit 1
fi

REMOTE="${PI_USER}@${PI_HOST}"

# Determine target virtual environment on the remote machine.
# Precedence: PI_VENV in .env -> ExecStart path in wavedisp.service -> ${PI_APP_DIR}/.venv
VENV_FROM_SERVICE="$(grep -E '^\s*ExecStart=' wavedisp.service | head -n1 | sed -E 's|^\s*ExecStart=([^ ]+)/bin/python.*|\1|' || true)"
DETECTED_VENV="${PI_VENV:-${VENV_FROM_SERVICE:-${PI_APP_DIR}/.venv}}"
if [[ "${DETECTED_VENV}" != /* ]]; then
  REMOTE_VENV="${PI_APP_DIR}/${DETECTED_VENV}"
else
  REMOTE_VENV="${DETECTED_VENV}"
fi

echo "Deploying WaveDisp to ${REMOTE}:${PI_APP_DIR} (venv: ${REMOTE_VENV})"

if [[ "${SKIP_DASHBOARD_BUILD}" != "1" ]]; then
  if [[ "${SKIP_DASHBOARD_INSTALL}" != "1" ]]; then
    echo "[1/5] Installing dashboard dependencies..."
    npm --prefix dashboard ci
  else
    echo "[1/5] Skipping dashboard dependencies install."
  fi
  echo "[2/5] Building React dashboard..."
  npm --prefix dashboard run build
else
  echo "[1/5] Skipping dashboard build."
fi

echo "[3/5] Preparing remote directories and copying project files..."
ssh "${REMOTE}" "mkdir -p '${PI_APP_DIR}/backend' '${PI_APP_DIR}/scripts' '${PI_APP_DIR}/dashboard/dist' '${PI_APP_DIR}/certs'"

# Device-local state (config, Spotify tokens, compiled fonts) is never overwritten.
rsync -a --exclude="__pycache__" --exclude="*.pyc" \
  --exclude="config.json" --exclude="config.json.tmp" \
  --exclude=".spotify_caches/" --exclude=".font_cache/" \
  backend/ "${REMOTE}:${PI_APP_DIR}/backend/"
rsync -a --exclude="__pycache__" --exclude="*.pyc" scripts/ "${REMOTE}:${PI_APP_DIR}/scripts/"
rsync -a dashboard/dist/ "${REMOTE}:${PI_APP_DIR}/dashboard/dist/"
rsync -a .env.example "${REMOTE}:${PI_APP_DIR}/.env.example"
if [ -f .env ]; then
  rsync -a .env "${REMOTE}:${PI_APP_DIR}/.env"
fi
if [ -d certs ]; then
  rsync -a certs/ "${REMOTE}:${PI_APP_DIR}/certs/"
fi
rsync -a requirements.txt "${REMOTE}:${PI_APP_DIR}/requirements.txt"
rsync -a wavedisp.service "${REMOTE}:${PI_APP_DIR}/wavedisp.service"

if [[ "${SKIP_REMOTE_DEPS}" != "1" ]]; then
  PIP_UPGRADE_FLAG=""
  if [[ "${UPGRADE_REMOTE_DEPS}" == "1" || "${UPGRADE_REMOTE_DEPS}" == "true" ]]; then
    echo "[4/5] Upgrading remote Python dependencies (--upgrade) in ${REMOTE_VENV}..."
    PIP_UPGRADE_FLAG="--upgrade"
  else
    echo "[4/5] Installing remote Python dependencies in ${REMOTE_VENV}..."
  fi
  ssh "${REMOTE}" "
    if [ ! -d '${REMOTE_VENV}' ]; then
      echo 'Creating virtual environment at ${REMOTE_VENV}...'
      python3 -m venv '${REMOTE_VENV}'
    fi
    '${REMOTE_VENV}/bin/pip' install ${PIP_UPGRADE_FLAG} -r '${PI_APP_DIR}/requirements.txt'
  "
else
  echo "[4/5] Skipping remote Python dependencies update."
fi

echo "[5/5] Installing service template and restarting..."
ssh "${REMOTE}" "sudo cp '${PI_APP_DIR}/wavedisp.service' '/etc/systemd/system/${PI_SERVICE_NAME}.service' && sudo systemctl daemon-reload && sudo systemctl enable '${PI_SERVICE_NAME}' && sudo systemctl restart '${PI_SERVICE_NAME}'"

echo "Deployment complete."
