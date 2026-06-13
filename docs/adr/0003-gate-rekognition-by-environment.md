# ADR 0003: Gate Rekognition behind an environment variable

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** project owner

## Context

Object detection uses Amazon Rekognition, which is unavailable on LocalStack's
free tier. The pipeline must still run end-to-end locally (resize, thumbnail,
metadata) without it, and the handler must behave identically in both
environments rather than branching on "am I running on LocalStack?".

## Decision

Control detection with an `ENABLE_REKOGNITION` environment variable, set to
`false` on LocalStack and `true` on AWS. The handler wraps the Rekognition call
in error handling so that, if the service is absent or fails, the rest of the
pipeline still completes and the `labels` field is simply empty.

## Consequences

### Positive
- One environment-agnostic handler; no environment-detection branching in code.
- Graceful degradation — a detection failure never breaks resize/metadata.

### Negative / trade-offs
- Object detection cannot be exercised locally; it is only verified on real AWS.
- Local and CI runs always produce empty `labels`, so that path relies on the
  AWS deploy for real validation.
