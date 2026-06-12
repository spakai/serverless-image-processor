#!/usr/bin/env bash
# Deploy the stack to LocalStack. Requires: docker compose up -d (LocalStack),
# plus `pip install terraform-local awscli-local`.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

bash "$ROOT/scripts/build.sh"

# Rekognition is unavailable on LocalStack community -> disable the call.
tflocal -chdir="$ROOT/infra" init -input=false
tflocal -chdir="$ROOT/infra" apply -auto-approve -input=false \
  -var="enable_rekognition=false"

echo
echo "Deployed to LocalStack. Try: bash scripts/seed-local.sh"
