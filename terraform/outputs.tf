output "destination_s3_bucket_name" {
  description = "The name of the S3 bucket where processed files are stored."
  value       = aws_s3_bucket.destination_bucket.bucket
}

output "destination_s3_bucket_arn" {
  description = "The ARN of the S3 bucket where processed files are stored."
  value       = aws_s3_bucket.destination_bucket.arn
}

# AWS Outputs
output "aws_region" {
  value = var.aws_region
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.task_tracking.name
}

output "aws_s3_destination_bucket" {
  description = "Name of the AWS S3 destination bucket"
  value       = module.aws.s3_destination_bucket
}

output "aws_ecr_repository_url" {
  description = "URL of the AWS ECR repository"
  value       = module.aws.ecr_repository_url
}

output "aws_dynamodb_table_name" {
  description = "Name of the AWS DynamoDB table for task tracking"
  value       = aws_dynamodb_table.task_tracking.name
}

output "aws_ecs_cluster_name" {
  description = "Name of the AWS ECS cluster"
  value       = module.aws.ecs_cluster_name
}

output "aws_ecs_service_name" {
  description = "Name of the AWS ECS service"
  value       = module.aws.ecs_service_name
}

output "aws_secrets_manager_secret_name" {
  description = "Name of the AWS Secrets Manager secret for GCP credentials"
  value       = module.aws.secrets_manager_secret_name
}

# GCP Outputs
output "gcp_project_id" {
  value = var.gcp_project_id
}

output "gcp_pubsub_dlq_topic" {
  description = "ID of the GCP Pub/Sub dead-letter topic"
  value       = module.gcp.pubsub_dlq_topic_id
}

output "gcp_firestore_database" {
  description = "ID of the GCP Firestore database"
  value       = module.gcp.firestore_database
}

output "gcp_secret_manager_secret_name" {
  description = "Name of the GCP Secret Manager secret for AWS credentials"
  value       = module.gcp.secret_manager_secret_name
}

output "gcp_processor_service_account" {
  description = "Email of the GCP service account for the processor"
  value       = module.gcp.processor_service_account
}

output "gcp_cloud_run_service_url" {
  description = "URL of the GCP Cloud Run service"
  value       = module.gcp.cloud_run_service_url
}

output "public_subnet_ids" {
  value = var.public_subnet_ids
}

output "private_subnet_ids" {
  value = var.private_subnet_ids
}

output "vpc_id" {
  value = var.vpc_id
} 