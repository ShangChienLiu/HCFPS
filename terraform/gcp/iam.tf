# Service account for Cloud Run processor service
resource "google_service_account" "processor_sa" {
  account_id   = "${var.project_prefix}-processor-sa"
  display_name = "Service Account for File Processor Cloud Run"
  description  = "Service account used by the file processor Cloud Run service"
}

# Service account for Pub/Sub to invoke Cloud Run
resource "google_service_account" "pubsub_sa" {
  account_id   = "${var.project_prefix}-pubsub-sa"
  display_name = "Service Account for Pub/Sub to invoke Cloud Run"
  description  = "Service account used by Pub/Sub to invoke Cloud Run services"
}

# Service account for DLQ handler
resource "google_service_account" "dlq_handler_sa" {
  account_id   = "${var.project_prefix}-dlq-handler-sa"
  display_name = "Service Account for DLQ Handler"
  description  = "Service account used for processing dead letter queues"
}

# IAM roles for processor service account
resource "google_project_iam_member" "processor_sa_roles" {
  for_each = toset([
    "roles/storage.admin",                # Access to GCS buckets
    "roles/pubsub.subscriber",            # Access to Pub/Sub
    "roles/pubsub.publisher",             # Publish to Pub/Sub
    "roles/firestore.dataWriter",         # Write to Firestore
    "roles/firestore.dataReader",         # Read from Firestore
    "roles/secretmanager.secretAccessor", # Access to Secret Manager
    "roles/logging.logWriter"             # Write to Cloud Logging
  ])
  
  project = var.gcp_project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.processor_sa.email}"
}

# IAM roles for Pub/Sub service account to invoke Cloud Run
resource "google_project_iam_member" "pubsub_sa_roles" {
  project = var.gcp_project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.pubsub_sa.email}"
}

# IAM roles for DLQ handler service account
resource "google_project_iam_member" "dlq_handler_sa_roles" {
  for_each = toset([
    "roles/storage.admin",                # Access to GCS buckets
    "roles/pubsub.subscriber",            # Access to Pub/Sub
    "roles/pubsub.publisher",             # Publish to Pub/Sub
    "roles/firestore.dataWriter",         # Write to Firestore
    "roles/secretmanager.secretAccessor", # Access to Secret Manager
    "roles/logging.logWriter"             # Write to Cloud Logging
  ])
  
  project = var.gcp_project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.dlq_handler_sa.email}"
}

# Allow service account to be impersonated for local development
resource "google_service_account_iam_binding" "processor_sa_user" {
  service_account_id = google_service_account.processor_sa.name
  role               = "roles/iam.serviceAccountUser"
  
  members = [
    "user:${var.developer_email}"
  ]
  
  # Only create if developer email is provided
  count = var.developer_email != "" ? 1 : 0
}
