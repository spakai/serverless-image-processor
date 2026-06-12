#!/usr/bin/env bash
# Deploy the SAME stack to real AWS. Requires AWS credentials configured
# (aws configure / SSO / env vars) and Terraform installed.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

bash "$ROOT/scripts/build.sh"

terraform -chdir="$ROOT/infra" init -input=false
terraform -chdir="$ROOT/infra" apply -input=false
# Rekognition stays enabled (default), so real labels come back on AWS.

echo
echo "Deployed to AWS. Upload an image under the uploads/ prefix to trigger it."
