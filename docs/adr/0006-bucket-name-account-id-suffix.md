# ADR 0006: Suffix the S3 bucket name with the AWS account ID

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** project owner

## Context

S3 bucket names are globally unique across all AWS accounts. The original name
`image-processor-dev-uploads` collided with an existing bucket somewhere on AWS,
and `terraform apply` failed with `BucketAlreadyExists` (HTTP 409).

## Decision

Append the deploying account's ID to the bucket name, sourced from
`data.aws_caller_identity.current.account_id`, giving names like
`image-processor-dev-uploads-<account-id>`. Account IDs are unique, so the
resulting bucket name is guaranteed unique, and reading the ID from the data
source keeps the config portable rather than hardcoding it.

## Consequences

### Positive
- Deploys reliably into any account without name collisions.
- No hardcoded account number; the config travels across accounts unchanged.

### Negative / trade-offs
- The bucket name is no longer human-memorable; consumers should read it from
  the Terraform `upload_bucket` output rather than assuming it.
