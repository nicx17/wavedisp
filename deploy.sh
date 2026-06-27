#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

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

echo "Deploying WaveDisp to ${REMOTE}:${PI_APP_DIR}"

if [[ "${SKIP_DASHBOARD_BUILD:-0}" != "1" ]]; then
  echo "[1/4] Building React dashboard..."
  npm --prefix dashboard run build
else
  echo "[1/4] Skipping dashboard build."
fi

echo "[2/4] Preparing remote directories..."
ssh "${REMOTE}" "mkdir -p '${PI_APP_DIR}/backend' '${PI_APP_DIR}/scripts' '${PI_APP_DIR}/dashboard/dist' '${PI_APP_DIR}/certs'"

echo "[3/4] Copying project files..."
rsync -a --exclude="__pycache__" --exclude="*.pyc" backend/ "${REMOTE}:${PI_APP_DIR}/backend/"
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

echo "[4/4] Installing service template and restarting..."
ssh "${REMOTE}" "sudo cp '${PI_APP_DIR}/wavedisp.service' '/etc/systemd/system/${PI_SERVICE_NAME}.service' && sudo systemctl daemon-reload && sudo systemctl enable '${PI_SERVICE_NAME}' && sudo systemctl restart '${PI_SERVICE_NAME}'"

echo "Deployment complete."
