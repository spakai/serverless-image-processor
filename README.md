# Serverless Image Processor

Upload an image to S3 → a Lambda resizes it, runs object detection
(Rekognition), and writes metadata to DynamoDB. The same Terraform deploys to
**LocalStack** (fast, free inner loop) and to **real AWS** (where Rekognition
actually runs). Built as a study project for **AWS SAA-C03** and **GH-600
(GitHub Agentic AI Developer)**.

## Architecture

```
Upload ──► S3 (uploads/) ──► Lambda ──┬─► S3 (resized/)
                                      ├─► Rekognition (labels)
                                      └─► DynamoDB (metadata)
```

The S3 event is filtered on the `uploads/` prefix, so the resized write to
`resized/` does not re-trigger the function (avoids an infinite, billable loop).

## Layout

```
infra/                 Terraform (S3, Lambda, DynamoDB, IAM, S3 notification)
src/processor/         Lambda handler + runtime requirements
tests/                 unit test (mocked) + integration test (LocalStack)
scripts/               build / deploy-local / deploy-aws / seed-local
docker-compose.yml     LocalStack
.github/workflows/     CI: lint + unit + LocalStack integration
```

## Prerequisites

- Docker, Python 3.12, Terraform >= 1.5
- `pip install -r requirements-dev.txt terraform-local awscli-local`
- A LocalStack auth token (free, non-commercial). Since 2026.03 LocalStack
  requires one even for free-tier services. Sign up at
  https://app.localstack.cloud, copy the token, and export it:
  `export LOCALSTACK_AUTH_TOKEN=ls-...`
  For CI, add it as a repo secret named `LOCALSTACK_AUTH_TOKEN`.

## Run locally (LocalStack)

```bash
docker compose up -d
bash scripts/deploy-local.sh   # builds the zip, applies via tflocal
bash scripts/seed-local.sh     # uploads a test image, prints the metadata row
```

Rekognition is **not** in LocalStack community, so `deploy-local.sh` sets
`enable_rekognition=false`. The resize + DynamoDB path is fully exercised; the
`labels` field comes back empty locally. That is expected.

## Run on real AWS

```bash
aws configure                  # or SSO / env credentials
bash scripts/deploy-aws.sh
aws s3 cp photo.jpg s3://image-processor-dev-uploads/uploads/photo.jpg
```

Here Rekognition runs for real and `labels` is populated. At learning volumes
this sits inside the AWS Free Tier (Lambda 1M req/mo, S3 5GB, DynamoDB 25GB,
Rekognition 5,000 images/mo for the first 12 months).

## Tests

```bash
pytest tests/test_handler.py                                  # no AWS needed
AWS_ENDPOINT_URL=http://localhost:4566 pytest tests/integration   # needs deploy-local
```

## Exam mapping

### AWS SAA-C03

| Project piece                          | SAA-C03 domain |
|----------------------------------------|----------------|
| S3 event → Lambda (decoupled trigger)  | Design resilient / event-driven architectures |
| `uploads/` prefix filter to stop loops | Cost-optimized design; understanding S3 events |
| Least-privilege IAM role + policy      | Design secure architectures |
| Lambda + Rekognition + DynamoDB        | Choose the right managed/serverless service |
| PAY_PER_REQUEST DynamoDB               | Cost-optimized data stores |
| Free-tier sizing                       | Cost-optimized architectures |

### GH-600 (GitHub Agentic AI Developer)

| Project piece                                  | GH-600 theme |
|------------------------------------------------|--------------|
| One IaC codebase, two targets (local → cloud)  | SDLC integration, safe promotion paths |
| CI runs against LocalStack before AWS          | Execution environments / guardrails |
| Approval before `deploy-aws`                   | Human-in-the-loop checkpoint |
| Same handler, env-gated Rekognition            | Reliable behaviour across environments |
| Tests an agent must keep green                 | Evaluation / error analysis of agent output |

## Using this for the agentic SDLC loop (GH-600)

Drive changes through an agent: it reads an issue, edits `handler.py` + `infra/`,
opens a PR. CI builds the zip, spins up LocalStack, applies the stack, and runs
both test layers — all free, every PR. A gated job promotes to AWS where
Rekognition fires. The pipeline *is* the exam content: tool use, execution
boundaries, guardrails, and evaluation.
