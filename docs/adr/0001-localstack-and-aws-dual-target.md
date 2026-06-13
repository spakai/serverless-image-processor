# ADR 0001: One Terraform codebase targeting LocalStack and AWS

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** project owner

## Context

The development loop needs to be fast and free — no AWS bills or credentials on
every iteration and every CI run. At the same time, the design must be validated
against real AWS, and the object-detection feature only works with the real
Amazon Rekognition service, which LocalStack's free tier does not provide.

## Decision

Use a single Terraform codebase in `infra/` deployed to two targets: LocalStack
(via the `tflocal` wrapper) for the local inner loop and CI, and real AWS (via
plain `terraform`) for production. Rekognition is disabled on LocalStack and
enabled on AWS.

## Consequences

### Positive
- Fast, free iteration; CI needs no AWS credentials.
- Infrastructure-as-code portability is proven by deploying the same files to
  both targets.

### Negative / trade-offs
- LocalStack emulates AWS but is not byte-for-byte identical; some behaviour
  only surfaces on real AWS.
- LocalStack has required an auth token even for free-tier services since the
  2026.03 release.
- A single local Terraform state directory means care is needed when switching
  between LocalStack and AWS targets on the same machine.
