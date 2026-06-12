# Spec 001 — Generate a thumbnail on upload

- **Status:** Ready for planning
- **Tracking issue:** #<!-- fill in once the GitHub issue is created -->
- **Author:** human (principal)

## Context

The pipeline currently produces one resized copy (longest side <= 1024px) per
upload. Consumers (e.g. a future gallery view) also need a small, uniform
thumbnail they can render in lists without downloading the larger image.

## User story

As a consumer of processed images, I want a small thumbnail generated
automatically on upload, so that I can display image previews cheaply.

## Acceptance criteria

Each criterion must be verifiable by an automated test.

- [ ] For every object created under `uploads/`, a corresponding object is
      created under `thumbnails/` with the same base filename.
- [ ] The thumbnail's longest side is <= 150px, with aspect ratio preserved
      (no stretching).
- [ ] The DynamoDB metadata record for the image gains a `thumbnail_key`
      attribute pointing at the `thumbnails/` object.
- [ ] Existing behaviour is unchanged: the `resized/` object and all current
      metadata fields are still produced exactly as before.
- [ ] Unit tests assert the thumbnail size and the new metadata field.
- [ ] The integration test confirms the `thumbnails/` object appears after an
      upload to a live LocalStack stack.
- [ ] `ruff check .` is clean and CI is green on the pull request.

## Out of scope

- Serving or exposing thumbnails via any API.
- Multiple thumbnail sizes — exactly one 150px thumbnail for now.
- Any change to the resize dimension or to Rekognition behaviour.

## Constraints

- Honour all guardrails in `AGENTS.md`. In particular: the new write goes under
  `thumbnails/`, the S3 event filter stays on `uploads/`, and `handler.py`
  stays environment-agnostic.
- No new AWS resources are expected (same bucket, new key prefix). If the plan
  finds otherwise, raise it before implementing.
