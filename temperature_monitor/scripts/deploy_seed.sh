#!/usr/bin/env bash
# Run during deployment, after the app is installed and DATABASE_URL is set,
# and before starting the server.
#
#   SEED_MOCK_DATA=true ./deploy_seed.sh            # seed only if empty (safe to repeat)
#   SEED_MOCK_DATA=true SEED_REFRESH=true ./deploy_seed.sh   # regenerate mock sensors' data
#
# Does nothing unless SEED_MOCK_DATA=true, so production stays clean by default.
set -euo pipefail

if [[ "${SEED_MOCK_DATA:-false}" != "true" ]]; then
  echo "[deploy] SEED_MOCK_DATA is not 'true' - skipping mock data seeding"
  exit 0
fi

cd "$(dirname "$0")"   # backend/app

ARGS=()
[[ "${SEED_REFRESH:-false}" == "true" ]] && ARGS+=(--refresh)
[[ -n "${SEED_DAYS:-}" ]] && ARGS+=(--days "$SEED_DAYS")

echo "[deploy] Seeding mock temperature data..."
python seed_mock_data.py "${ARGS[@]}"
