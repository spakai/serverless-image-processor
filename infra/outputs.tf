output "upload_bucket" {
  value = aws_s3_bucket.uploads.bucket
}

output "metadata_table" {
  value = aws_dynamodb_table.metadata.name
}

output "lambda_name" {
  value = aws_lambda_function.processor.function_name
}
