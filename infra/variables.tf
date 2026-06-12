variable "project_name" {
  type    = string
  default = "image-processor"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

# Real AWS turns Rekognition on. LocalStack community has no Rekognition,
# so deploy-local.sh sets this to false to skip the call entirely.
variable "enable_rekognition" {
  type    = bool
  default = true
}
