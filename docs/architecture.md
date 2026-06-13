# Architecture

Architecture of the Serverless Image Processor, described with the
[C4 model](https://c4model.com/) at three zoom levels: System Context,
Container, and Component. Diagrams are Mermaid and render on GitHub.

> Note: Mermaid's C4 support is still experimental, so layout can be a little
> rough. If a diagram renders cramped, the element/relationship tables under
> each one describe the same thing in text.

## Level 1 — System Context

The big picture: who uses the system and what external services it depends on.

```mermaid
C4Context
    title System Context — Serverless Image Processor

    Person(uploader, "Uploader", "Sends images to be processed and reads the results")
    System(sip, "Serverless Image Processor", "Resizes images, generates thumbnails, detects objects, stores metadata")
    System_Ext(rekognition, "Amazon Rekognition", "Managed computer-vision service (DetectLabels)")

    Rel(uploader, sip, "Uploads images, reads results", "AWS SDK / S3 API")
    Rel(sip, rekognition, "Requests object labels", "HTTPS / AWS SDK")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

| Element | Type | Responsibility |
|---|---|---|
| Uploader | Person | Puts an image into the system and consumes the processed outputs |
| Serverless Image Processor | System | The thing this repo builds |
| Amazon Rekognition | External system | AWS-managed object detection, called at runtime |

## Level 2 — Container

The deployable/runtime pieces inside the system and how they interact.

```mermaid
C4Container
    title Container Diagram — Serverless Image Processor

    Person(uploader, "Uploader", "Sends images, reads results")

    System_Boundary(sip, "Serverless Image Processor") {
        Container(bucket, "Image Bucket", "Amazon S3", "Holds originals (uploads/), resized images (resized/), and thumbnails (thumbnails/)")
        Container(lambda, "Processor Function", "AWS Lambda · Python 3.12 · Pillow", "Resizes, generates thumbnail, requests detection, writes metadata")
        ContainerDb(table, "Metadata Table", "Amazon DynamoDB", "One record per image: keys, sizes, labels, timestamp")
    }

    System_Ext(rekognition, "Amazon Rekognition", "DetectLabels")

    Rel(uploader, bucket, "Uploads image to uploads/", "S3 PutObject")
    Rel(bucket, lambda, "ObjectCreated (uploads/ only)", "S3 Event Notification")
    Rel(lambda, bucket, "Reads original; writes resized/ + thumbnails/", "S3 Get/PutObject")
    Rel(lambda, rekognition, "Detects objects", "HTTPS")
    Rel(lambda, table, "Writes metadata", "PutItem")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

| Container | Technology | Notes |
|---|---|---|
| Image Bucket | Amazon S3 | Single bucket, three prefixes. The event filter on `uploads/` is what stops the `resized/`/`thumbnails/` writes from re-triggering the function (see ADR 0002). |
| Processor Function | AWS Lambda, Python 3.12 | Stateless; the same code runs on LocalStack and AWS (see ADR 0003). |
| Metadata Table | Amazon DynamoDB | `image_key` partition key, `PAY_PER_REQUEST`. |

## Level 3 — Component

Inside the Processor Function — the steps within `handler.py`.

```mermaid
C4Component
    title Component Diagram — Processor Function (handler.py)

    Container_Boundary(lambda, "Processor Function") {
        Component(handler, "Event Handler", "handler()", "Parses the S3 event, iterates records")
        Component(resize, "Resize Step", "Pillow", "Downscale to <=1024px longest side -> resized/")
        Component(thumb, "Thumbnail Step", "Pillow", "Downscale to <=150px -> thumbnails/")
        Component(detect, "Detection Step", "boto3", "Calls Rekognition; tolerates its absence")
        Component(persist, "Metadata Writer", "boto3", "Writes one record to DynamoDB")
    }

    Rel(handler, resize, "invokes")
    Rel(handler, thumb, "invokes")
    Rel(handler, detect, "invokes")
    Rel(handler, persist, "invokes")
```

## Key runtime flow

1. Uploader writes an object under `uploads/`.
2. S3 emits an `ObjectCreated` event (only for the `uploads/` prefix).
3. The event invokes the Lambda.
4. The Lambda reads the original bytes once, then:
   - writes a resized copy to `resized/`,
   - writes a 150px thumbnail to `thumbnails/`,
   - calls Rekognition `DetectLabels` (skipped/empty when disabled),
   - writes a metadata record to DynamoDB.

## Deployment targets

The same Terraform in `infra/` deploys to two targets:

- **LocalStack** (local + CI) — via `tflocal`; Rekognition disabled.
- **Real AWS** (production) — via `terraform`; Rekognition enabled.

See ADR 0001 for the rationale and trade-offs.
