# ADR 0004: Package the Lambda as a zip with a manylinux Pillow wheel

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** project owner

## Context

Pillow includes compiled native code, so the installed package must match the
Lambda runtime (Amazon Linux, x86_64, Python 3.12) — not the developer's
machine. A container-image Lambda would also work but requires ECR, which is not
in LocalStack's free tier, complicating the local loop.

## Decision

Ship a zip-packaged Lambda. The build script installs Pillow with
`--platform manylinux2014_x86_64` for CPython 3.12 into a build directory,
adds the handler, and zips it. Terraform references the prebuilt
`build/processor.zip`.

## Consequences

### Positive
- Runs on both LocalStack community and real AWS without an image registry.
- Small, fast deployment artifact.

### Negative / trade-offs
- `build.sh` must run before any `terraform apply` (the deploy scripts do this).
- The platform/Python pins must be updated if the Lambda runtime version changes.
