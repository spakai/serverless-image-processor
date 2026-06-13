# Plan 001 — Generate a thumbnail on upload

- **Status:** APPROVED
- **Spec:** ./spec.md

## Approach

A new step is inserted in `process_one` immediately after the existing resize. A fresh `Image` is opened from `raw` (the original bytes already in memory — no extra S3 read) so the thumbnail is derived from the *original* dimensions rather than the already-downscaled image. `img.thumbnail((THUMBNAIL_MAX_DIMENSION, THUMBNAIL_MAX_DIMENSION))` is called on that fresh object (Pillow preserves aspect ratio in-place) and the result is serialised in the original image format and uploaded under `thumbnails/<base_filename>`. Two env-var-backed constants (`THUMBNAIL_PREFIX`, `THUMBNAIL_MAX_DIMENSION`) with safe defaults keep the handler environment-agnostic. `thumbnail_key` is added to the DynamoDB `put_item` call and the returned dict. All existing steps and outputs are unchanged.

The `thumbnails/` prefix is safe against re-triggering: the S3 notification filter is `uploads/`; the same bucket, different prefix write never fires the Lambda again.

## Files to change

| File | Change |
|------|--------|
| `src/processor/handler.py` | Add `THUMBNAIL_PREFIX` (default `"thumbnails/"`) and `THUMBNAIL_MAX_DIMENSION` (default `150`) env-var constants. After the resize block, open a new `Image` from `raw`, call `.thumbnail((THUMBNAIL_MAX_DIMENSION, THUMBNAIL_MAX_DIMENSION))`, serialise to BytesIO using `img_format`, `put_object` to `thumbnails/<base>`. Add `thumbnail_key` to DynamoDB item and returned dict. |
| `tests/test_handler.py` | Update `test_resize_detect_and_persist`: switch to `call_args_list` (two `put_object` calls now); assert index 0 = `resized/photo.jpg` with max side ≤ 1024; assert index 1 = `thumbnails/photo.jpg`; open thumbnail bytes and assert `size == (150, 113)` for the 2000×1500 input (proving aspect ratio and max-side constraint together — 150×150 would fail); assert `put_item` item contains `thumbnail_key`. Update `test_pipeline_survives_missing_rekognition`: assert `thumbnail_key` still present in `put_item` item. |
| `tests/integration/test_localstack.py` | Add `thumbnail_key` poll alongside `resized_key`; include `thumbnail_found` in loop exit condition and final assertions. |
| `infra/main.tf` | Add `THUMBNAIL_PREFIX = "thumbnails/"` and `THUMBNAIL_MAX_DIMENSION = "150"` to the Lambda `environment.variables` block. No new resources. |

## Test plan

| Acceptance criterion | Test |
|---|---|
| AC1 — `thumbnails/` object with same base filename | Unit: `call_args_list[1].kwargs["Key"] == "thumbnails/photo.jpg"` |
| AC2 — longest side ≤ 150px, **aspect ratio preserved** | Unit: open thumbnail bytes; `assert thumb.size == (150, 113)` — a 150×150 result would fail |
| AC3 — DynamoDB gains `thumbnail_key` | Unit: `put_item` Item contains `"thumbnail_key": {"S": "thumbnails/photo.jpg"}` |
| AC4 — existing behaviour unchanged | Unit: `call_args_list[0].kwargs["Key"] == "resized/photo.jpg"` and all pre-existing DynamoDB fields still present; `test_pipeline_survives_missing_rekognition` passes |
| AC5 — unit tests assert size + metadata field | Covered by AC2 + AC3 assertions |
| AC6 — integration test confirms `thumbnails/` object | Integration: poll `head_object` for `thumbnail_key`; assert `thumbnail_found` |
| AC7 — `ruff check .` clean, CI green | Constants follow existing style; no new imports needed |

## Risks / open questions

- **Image mutation:** `img.thumbnail()` mutates in-place. The thumbnail step opens a *new* `Image` from `raw` so resize and thumbnail are independent and both derived from original dimensions.
- **`call_args` vs `call_args_list`:** The existing assertion uses `call_args` (last call only). After this change `put_object` is called twice; tests use `call_args_list[0]` / `[1]` to avoid silent misdirection.
- No open questions requiring a human decision before implementation.

## Infrastructure impact

No new resources. The IAM `ReadWriteUploads` statement covers `${bucket_arn}/*`, which includes `thumbnails/`. The S3 event filter stays on `uploads/`. The only `infra/main.tf` change is two additive entries in the Lambda `environment.variables` block.

---

## Human approval

- [x] I have read this plan and approve implementation.
- **Approved by:** human (principal), 2026-06-12
- **Notes / required changes:** (1) AC2 test must assert exact dimensions (150×112) not just max-side; (2) use THUMBNAIL_MAX_DIMENSION constant in .thumbnail() call; (3) save thumbnail in original image format.
