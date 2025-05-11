# Random suffix to ensure globally unique bucket names
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Temporary S3 bucket for file uploads
resource "aws_s3_bucket" "temp_bucket" {
  bucket        = "${var.project_prefix}-temp-uploads-${random_string.bucket_suffix.result}"
  force_destroy = true
}

# Configure lifecycle policy to automatically delete old files
resource "aws_s3_bucket_lifecycle_configuration" "temp_bucket_lifecycle" {
  bucket = aws_s3_bucket.temp_bucket.id

  rule {
    id     = "delete-old-files"
    status = "Enabled"

    expiration {
      days = 7  # Delete files after 7 days
    }
  }
}

# Destination S3 bucket for processed files
resource "aws_s3_bucket" "destination_bucket" {
  bucket        = "${var.project_prefix}-processed-files-${random_string.bucket_suffix.result}"
  force_destroy = true
}

# Configure public access blocks for both buckets
resource "aws_s3_bucket_public_access_block" "temp_bucket_access_block" {
  bucket = aws_s3_bucket.temp_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "destination_bucket_access_block" {
  bucket = aws_s3_bucket.destination_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CORS configuration for the temp bucket to allow file uploads from web UI
resource "aws_s3_bucket_cors_configuration" "temp_bucket_cors" {
  bucket = aws_s3_bucket.temp_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "HEAD"]
    allowed_origins = ["*"]  # Should be restricted in production
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
