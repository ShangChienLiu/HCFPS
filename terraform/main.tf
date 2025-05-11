# main.tf - Entry point for the Terraform configuration

# Define required providers
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.34"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }

  required_version = ">= 1.2.0"
  
  # Optional: Backend configuration for state storage
  # backend "s3" {
  #   bucket         = "terraform-state-bucket"
  #   key            = "multi-cloud-processor/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-locks"
  #   encrypt        = true
  # }
}

# AWS Provider Configuration
provider "aws" {
  region = var.aws_region
  
  # If running outside of AWS & need to specify credentials
  access_key = var.aws_access_key_id != "" ? var.aws_access_key_id : null
  secret_key = var.aws_secret_access_key != "" ? var.aws_secret_access_key : null
  
  default_tags {
    tags = {
      ManagedBy   = "Terraform"
      Project     = "MultiCloudFileProcessor"
      Environment = "prod"
    }
  }
}

# GCP Provider Configuration
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
  credentials = file(var.gcp_credentials_file)
}

# Random provider for generating unique IDs
provider "random" {}

# Pass variables to AWS module
module "aws" {
  source = "./aws"
  
  # Variables
  project_prefix      = var.project_prefix
  aws_region          = var.aws_region
  vpc_id              = var.vpc_id
  private_subnet_ids  = var.private_subnet_ids
  public_subnet_ids   = var.public_subnet_ids
  dynamodb_table_name = aws_dynamodb_table.task_tracking.name
  dynamodb_table_arn  = aws_dynamodb_table.task_tracking.arn
  gcp_project_id      = var.gcp_project_id
  common_tags         = var.common_tags
  enable_secret_rotation = var.enable_secret_rotation
  dlq_notification_email = var.dlq_notification_email
  
  # Fargate configuration
  fargate_cpu       = var.fargate_cpu
  fargate_memory    = var.fargate_memory
  min_capacity      = var.min_capacity
  max_capacity      = var.max_capacity
}

# Pass variables to GCP module
module "gcp" {
  source = "./gcp"
  
  # Variables
  project_prefix = var.project_prefix
  gcp_region     = var.gcp_region
  gcp_project_id = var.gcp_project_id
  aws_region     = var.aws_region
  common_labels  = var.common_labels
}

# Add random string resource for unique S3 bucket name
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Destination S3 bucket for all processed files
resource "aws_s3_bucket" "destination_bucket" {
  bucket = "${var.destination_s3_bucket_name}-${random_string.bucket_suffix.result}"

  tags = merge(
    var.common_tags,
    {
      Name = "${var.destination_s3_bucket_name}-destination"
    }
  )
}

resource "aws_s3_bucket_public_access_block" "destination_bucket_access_block" {
  bucket                  = aws_s3_bucket.destination_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "destination_bucket_versioning" {
  bucket = aws_s3_bucket.destination_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
} 