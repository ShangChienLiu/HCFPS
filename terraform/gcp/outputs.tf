# GCP Module Outputs

output "pubsub_topic_id" {
  description = "ID of the Pub/Sub topic for file processing tasks"
  value       = google_pubsub_topic.file_processing_tasks.id
}

output "pubsub_dlq_topic_id" {
  description = "ID of the Pub/Sub dead-letter topic"
  value       = google_pubsub_topic.file_processing_dlq.id
}

output "pubsub_subscription_id" {
  description = "ID of the Pub/Sub subscription"
  value       = google_pubsub_subscription.task_subscription.id
}

output "cloud_run_service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_service.processor.status[0].url
}

output "gcs_temp_bucket" {
  description = "Name of the Cloud Storage temporary bucket"
  value       = google_storage_bucket.temp_bucket.name
}

output "gcs_destination_bucket" {
  description = "Name of the Cloud Storage destination bucket"
  value       = google_storage_bucket.destination_bucket.name
}

output "firestore_database" {
  description = "ID of the Firestore database"
  value       = google_firestore_database.task_tracking.name
}

output "secret_manager_secret_name" {
  description = "Name of the Secret Manager secret for AWS credentials"
  value       = google_secret_manager_secret.aws_credentials.name
}

output "processor_service_account" {
  description = "Email of the service account for the processor"
  value       = google_service_account.processor_sa.email
} 