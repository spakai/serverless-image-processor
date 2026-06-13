provider "aws" {
  region = var.aws_region
}

locals {
  name = "${var.project_name}-${var.environment}"
}

# --- S3: single bucket, uploads/ in and resized/ out -------------------------
resource "aws_s3_bucket" "uploads" {
  bucket = "${local.name}-uploads"
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket                  = aws_s3_bucket.uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- DynamoDB: one item per processed image ----------------------------------
resource "aws_dynamodb_table" "metadata" {
  name         = "${local.name}-metadata"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "image_key"

  attribute {
    name = "image_key"
    type = "S"
  }
}

# --- IAM: least-privilege role for the Lambda --------------------------------
data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${local.name}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

data "aws_iam_policy_document" "lambda" {
  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
  statement {
    sid       = "ReadWriteUploads"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.uploads.arn}/*"]
  }
  statement {
    sid       = "WriteMetadata"
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.metadata.arn]
  }
  statement {
    sid       = "DetectLabels"
    actions   = ["rekognition:DetectLabels"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "${local.name}-lambda-policy"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda.json
}

# --- Lambda: built by scripts/build.sh into ../build/processor.zip -----------
resource "aws_lambda_function" "processor" {
  function_name    = "${local.name}-processor"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 512
  filename         = "${path.module}/../build/processor.zip"
  source_code_hash = filebase64sha256("${path.module}/../build/processor.zip")

  environment {
    variables = {
      METADATA_TABLE         = aws_dynamodb_table.metadata.name
      RESIZED_PREFIX         = "resized/"
      MAX_DIMENSION          = "1024"
      THUMBNAIL_PREFIX       = "thumbnails/"
      THUMBNAIL_MAX_DIMENSION = "150"
      ENABLE_REKOGNITION     = tostring(var.enable_rekognition)
    }
  }
}

# --- Wiring: ObjectCreated under uploads/ invokes the Lambda -----------------
# filter_prefix = "uploads/" is what stops the resized/ write from
# re-triggering the function (an easy and expensive infinite loop otherwise).
resource "aws_lambda_permission" "s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.uploads.arn
}

resource "aws_s3_bucket_notification" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
  }

  depends_on = [aws_lambda_permission.s3]
}
