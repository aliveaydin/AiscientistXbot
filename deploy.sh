#!/usr/bin/env bash
# One-command deploy for the Kualia VPS.
# Pulls the latest origin/main and rebuilds the containers.
# Run on the server:  cd /root/twitter-bot && ./deploy.sh
set -euo pipefail

cd "$(dirname "$0")"

# Use the read-only deploy key for git (no interactive auth on the server).
if [ -f /root/.ssh/kualia_deploy ]; then
  export GIT_SSH_COMMAND="ssh -i /root/.ssh/kualia_deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
fi

echo "==> git pull --ff-only origin main"
git pull --ff-only origin main

echo "==> docker compose up -d --build"
docker compose up -d --build

echo "==> containers:"
docker compose ps

echo "==> waiting for bot to become healthy..."
code=000
for i in $(seq 1 20); do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/health || echo 000)
  if [ "$code" = "200" ]; then break; fi
  sleep 2
done
echo "bot /health: $code"
if [ "$code" != "200" ]; then
  echo "!! bot did not report healthy after ~40s — check: docker compose logs --tail=50 bot" >&2
  exit 1
fi

echo "==> deploy complete."
