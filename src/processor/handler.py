"""S3-triggered image processor: resize -> object detection -> metadata.

The SAME handler runs on LocalStack and on real AWS. The only behavioural
difference is Rekognition: on real AWS it returns real labels; on LocalStack
community it is unavailable, so the call is wrapped to keep the pipeline green.
"""
import io
import json
import os
import urllib.parse
from datetime import datetime, timezone

import boto3
from PIL import Image

METADATA_TABLE = os.environ["METADATA_TABLE"]
RESIZED_PREFIX = os.environ.get("RESIZED_PREFIX", "resized/")
MAX_DIMENSION = int(os.environ.get("MAX_DIMENSION", "1024"))
ENABLE_REKOGNITION = os.environ.get("ENABLE_REKOGNITION", "true").lower() == "true"

# LocalStack injects AWS_ENDPOINT_URL into the Lambda env. boto3 honours it on
# recent versions, but we pass it explicitly so behaviour is identical anywhere.
_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL") or None


def _client(service):
    return boto3.client(service, endpoint_url=_ENDPOINT)


s3 = _client("s3")
dynamodb = _client("dynamodb")
rekognition = _client("rekognition")


def handler(event, context):
    return {"processed": [
        process_one(r["s3"]["bucket"]["name"],
                    urllib.parse.unquote_plus(r["s3"]["object"]["key"]))
        for r in event.get("Records", [])
    ]}


def process_one(bucket, key):
    raw = s3.get_object(Bucket=bucket, Key=key)["Body"].read()

    # 1. Resize -------------------------------------------------------------
    img = Image.open(io.BytesIO(raw))
    img_format = img.format or "JPEG"
    width, height = img.size
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
    new_width, new_height = img.size

    buf = io.BytesIO()
    img.save(buf, format=img_format)
    resized_key = RESIZED_PREFIX + key.split("/", 1)[-1]
    s3.put_object(Bucket=bucket, Key=resized_key, Body=buf.getvalue())

    # 2. Object detection ---------------------------------------------------
    # Real on AWS; absent on LocalStack community -> caught, pipeline stays green.
    labels = []
    if ENABLE_REKOGNITION:
        try:
            resp = rekognition.detect_labels(
                Image={"S3Object": {"Bucket": bucket, "Name": key}},
                MaxLabels=10,
                MinConfidence=70,
            )
            labels = [{"name": lab["Name"], "confidence": round(lab["Confidence"], 2)}
                      for lab in resp.get("Labels", [])]
        except Exception as exc:  # noqa: BLE001 - resilient by design
            print(f"rekognition skipped ({type(exc).__name__}): {exc}")

    # 3. Persist metadata ---------------------------------------------------
    dynamodb.put_item(TableName=METADATA_TABLE, Item={
        "image_key": {"S": key},
        "resized_key": {"S": resized_key},
        "original_size": {"S": f"{width}x{height}"},
        "resized_size": {"S": f"{new_width}x{new_height}"},
        "format": {"S": img_format},
        "labels": {"S": json.dumps(labels)},
        "processed_at": {"S": datetime.now(timezone.utc).isoformat()},
    })

    return {"key": key, "resized_key": resized_key, "labels": labels}
