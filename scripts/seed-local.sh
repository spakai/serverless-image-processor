#!/usr/bin/env bash
# Generate a test image, upload it under uploads/ to trigger the pipeline,
# then read the resized object and the DynamoDB metadata back out.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

BUCKET="$(tflocal -chdir="$ROOT/infra" output -raw upload_bucket)"
TABLE="$(tflocal -chdir="$ROOT/infra" output -raw metadata_table)"
KEY="uploads/sample-$(date +%s).png"

python3 - "$ROOT/sample.png" <<'PY'
import sys
from PIL import Image
Image.new("RGB", (1600, 1200), "skyblue").save(sys.argv[1], format="PNG")
PY

echo "Uploading $KEY ..."
awslocal s3 cp "$ROOT/sample.png" "s3://$BUCKET/$KEY"

echo "Waiting for the Lambda to run ..."
sleep 6

echo
echo "Objects in bucket:"
awslocal s3 ls "s3://$BUCKET/" --recursive

echo
echo "Metadata row:"
awslocal dynamodb get-item --table-name "$TABLE" \
  --key "{\"image_key\": {\"S\": \"$KEY\"}}"
