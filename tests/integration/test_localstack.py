"""Integration test against a LIVE LocalStack stack.

Assumes `scripts/deploy-local.sh` has already applied the Terraform so the
bucket, Lambda, trigger and table exist. Uploads an image under uploads/,
then polls for the resized object and the DynamoDB metadata item.

Run: AWS_ENDPOINT_URL=http://localhost:4566 pytest tests/integration -v
"""
import io
import os
import time

import boto3
import pytest
from PIL import Image

ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")
BUCKET = os.environ.get("UPLOAD_BUCKET", "image-processor-dev-uploads")
TABLE = os.environ.get("METADATA_TABLE", "image-processor-dev-metadata")

# LocalStack accepts any credentials; these keep boto3 from complaining.
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")


def _reachable():
    try:
        boto3.client("s3", endpoint_url=ENDPOINT).list_buckets()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _reachable(), reason="LocalStack not reachable at AWS_ENDPOINT_URL"
)


def _png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (1800, 1200), color="green").save(buf, format="PNG")
    return buf.getvalue()


def test_upload_triggers_pipeline():
    s3 = boto3.client("s3", endpoint_url=ENDPOINT)
    ddb = boto3.client("dynamodb", endpoint_url=ENDPOINT)

    key = f"uploads/it-{int(time.time())}.png"
    s3.put_object(Bucket=BUCKET, Key=key, Body=_png_bytes())

    base = key.split("/", 1)[1]
    resized_key = "resized/" + base
    thumbnail_key = "thumbnails/" + base

    resized_found = False
    thumbnail_found = False
    item_found = False
    for _ in range(30):  # ~30s budget for async Lambda
        time.sleep(1)
        try:
            s3.head_object(Bucket=BUCKET, Key=resized_key)
            resized_found = True
        except Exception:
            pass
        try:
            s3.head_object(Bucket=BUCKET, Key=thumbnail_key)
            thumbnail_found = True
        except Exception:
            pass
        got = ddb.get_item(TableName=TABLE, Key={"image_key": {"S": key}})
        if "Item" in got:
            item_found = True
        if resized_found and thumbnail_found and item_found:
            break

    assert resized_found, f"resized object {resized_key} was never created"
    assert thumbnail_found, f"thumbnail object {thumbnail_key} was never created"
    assert item_found, f"metadata row for {key} was never written"
