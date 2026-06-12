"""Unit test: real Pillow resize logic, mocked AWS clients. No AWS/LocalStack.

Run: pytest tests/test_handler.py -v
"""
import io
import os
import sys
from unittest.mock import MagicMock

from PIL import Image

os.environ.setdefault("METADATA_TABLE", "test-table")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")  # Lambda always has one
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "processor"))

import handler  # noqa: E402


def _make_image(width=2000, height=1500):
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color="blue").save(buf, format="JPEG")
    return buf.getvalue()


def test_resize_detect_and_persist(monkeypatch):
    fake_s3 = MagicMock()
    fake_s3.get_object.return_value = {"Body": io.BytesIO(_make_image())}
    fake_dynamo = MagicMock()
    fake_rek = MagicMock()
    fake_rek.detect_labels.return_value = {
        "Labels": [{"Name": "Sky", "Confidence": 99.12}]
    }

    monkeypatch.setattr(handler, "s3", fake_s3)
    monkeypatch.setattr(handler, "dynamodb", fake_dynamo)
    monkeypatch.setattr(handler, "rekognition", fake_rek)

    result = handler.process_one("my-bucket", "uploads/photo.jpg")

    assert result["resized_key"] == "resized/photo.jpg"
    assert result["thumbnail_key"] == "thumbnails/photo.jpg"
    assert result["labels"] == [{"name": "Sky", "confidence": 99.12}]

    calls = fake_s3.put_object.call_args_list
    assert len(calls) == 2

    # AC4 — resized/ object still produced with correct key and size
    resized_call = calls[0].kwargs
    assert resized_call["Key"] == "resized/photo.jpg"
    resized = Image.open(io.BytesIO(resized_call["Body"]))
    assert max(resized.size) <= handler.MAX_DIMENSION

    # AC1 — thumbnails/ object created with same base filename
    thumb_call = calls[1].kwargs
    assert thumb_call["Key"] == "thumbnails/photo.jpg"

    # AC2 — longest side <= 150px AND aspect ratio preserved
    # 2000x1500 -> scale = 150/2000 = 0.075 -> 150x112.5 -> Pillow rounds to 150x113
    thumb = Image.open(io.BytesIO(thumb_call["Body"]))
    assert thumb.size == (150, 113), f"expected (150, 113), got {thumb.size}"

    # AC3 — DynamoDB record gains thumbnail_key
    fake_dynamo.put_item.assert_called_once()
    item = fake_dynamo.put_item.call_args.kwargs["Item"]
    assert item["thumbnail_key"] == {"S": "thumbnails/photo.jpg"}


def test_pipeline_survives_missing_rekognition(monkeypatch):
    """LocalStack community has no Rekognition -> the call raises and is caught."""
    fake_s3 = MagicMock()
    fake_s3.get_object.return_value = {"Body": io.BytesIO(_make_image())}
    fake_dynamo = MagicMock()
    fake_rek = MagicMock()
    fake_rek.detect_labels.side_effect = Exception("service not available")

    monkeypatch.setattr(handler, "s3", fake_s3)
    monkeypatch.setattr(handler, "dynamodb", fake_dynamo)
    monkeypatch.setattr(handler, "rekognition", fake_rek)

    result = handler.process_one("my-bucket", "uploads/photo.jpg")

    assert result["labels"] == []
    assert result["thumbnail_key"] == "thumbnails/photo.jpg"
    fake_dynamo.put_item.assert_called_once()  # metadata still written
    item = fake_dynamo.put_item.call_args.kwargs["Item"]
    assert "thumbnail_key" in item
