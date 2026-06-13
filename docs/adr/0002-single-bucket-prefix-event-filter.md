# ADR 0002: Single bucket with prefix-scoped event notification

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** project owner

## Context

The function writes its outputs (resized image, thumbnail) back into object
storage. If those writes land in a location that also triggers the function,
each upload causes an unbounded chain of invocations — an infinite, billable
loop.

## Decision

Use one S3 bucket with three prefixes: inputs under `uploads/`, outputs under
`resized/` and `thumbnails/`. Scope the S3 `ObjectCreated` event notification to
the `uploads/` prefix only, so output writes never re-trigger the function.

## Consequences

### Positive
- Simple single-bucket topology.
- No recursive invocation; outputs can safely share the bucket with inputs.

### Negative / trade-offs
- All prefixes share one bucket's policies and lifecycle.
- The `uploads/` event filter is load-bearing: broadening or removing it
  reintroduces the loop. This is recorded as a guardrail in `AGENTS.md`.
