# Architecture Decision Records

Short documents capturing significant architectural decisions: the context, the
decision, and its consequences. Format follows Michael Nygard's ADR style.

## How to use

- Add a new ADR by copying `0000-adr-template.md` to the next number, e.g.
  `0007-some-decision.md`.
- One decision per file. Keep it short. Never edit a decided ADR to reverse it —
  instead add a new ADR and mark the old one `Superseded by ADR-XXXX`.
- A decision is "significant" if it is costly to reverse, affects structure, or
  future-you would ask "why was it done this way?".

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-localstack-and-aws-dual-target.md) | One Terraform codebase targeting LocalStack and AWS | Accepted |
| [0002](0002-single-bucket-prefix-event-filter.md) | Single bucket with prefix-scoped event notification | Accepted |
| [0003](0003-gate-rekognition-by-environment.md) | Gate Rekognition behind an environment variable | Accepted |
| [0004](0004-package-lambda-zip-manylinux-pillow.md) | Package the Lambda as a zip with a manylinux Pillow wheel | Accepted |
| [0005](0005-terraform-as-iac-tool.md) | Use Terraform (with tflocal) as the IaC tool | Accepted |
| [0006](0006-bucket-name-account-id-suffix.md) | Suffix the S3 bucket name with the AWS account ID | Accepted |
