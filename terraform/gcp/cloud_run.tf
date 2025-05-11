# Cloud Run service for processing tasks
resource "google_cloud_run_service" "processor" {
  name     = "${var.project_prefix}-processor"
  location = var.gcp_region

  template {
    spec {
      containers {
        image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.processor_repo.repository_id}/processor:latest"
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "2Gi"
          }
        }
        
        env {
          name  = "CLOUD_PROVIDER"
          value = "gcp"
        }
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.gcp_project_id
        }
        
        env {
          name  = "PUBSUB_TOPIC"
          value = google_pubsub_topic.file_processing_tasks.name
        }
        
        env {
          name  = "GCS_TEMP_BUCKET"
          value = google_storage_bucket.temp_bucket.name
        }
        
        env {
          name  = "GCS_DESTINATION_BUCKET"
          value = google_storage_bucket.destination_bucket.name
        }
        
        env {
          name  = "FIRESTORE_COLLECTION"
          value = "tasks"
        }
        
        # Reference to secret for AWS credentials
        env {
          name = "AWS_CREDENTIALS"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.aws_credentials.secret_id
              key  = "latest"
            }
          }
        }
      }
      
      # Service account for the Cloud Run service
      service_account_name = google_service_account.processor_sa.email
      
      # Timeout for processing tasks
      timeout_seconds = 900
    }
    
    # Automatic scaling
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "10"
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  autogenerate_revision_name = true
}

# IAM binding for Pub/Sub to invoke Cloud Run
resource "google_cloud_run_service_iam_binding" "processor_invoker" {
  location = google_cloud_run_service.processor.location
  service  = google_cloud_run_service.processor.name
  role     = "roles/run.invoker"
  members  = [
    "serviceAccount:${google_service_account.pubsub_sa.email}"
  ]
}
