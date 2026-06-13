# ADR 0005: Use Terraform (with tflocal) as the IaC tool

- **Status:** Accepted
- **Date:** 2026-06-12
- **Deciders:** project owner

## Context

The project needs one infrastructure-as-code definition that can target both
LocalStack and real AWS. Candidates were Terraform, AWS SAM, and AWS CDK. A
clean local/cloud story and a broadly transferable skill mattered more than
AWS-native serverless ergonomics.

## Decision

Use Terraform. For LocalStack, the `tflocal` wrapper redirects the AWS provider
endpoints with no change to the `.tf` files; for AWS, the same files run under
plain `terraform`.

## Consequences

### Positive
- Clean dual-target deploys with `tflocal` / `terraform` over identical config.
- Terraform is a widely applicable skill beyond this project.

### Negative / trade-offs
- Less serverless-specific convenience than AWS SAM (e.g. local invoke, guided
  deploys).
- Local state lives in a single directory, so switching targets on one machine
  needs care (see ADR 0001).
