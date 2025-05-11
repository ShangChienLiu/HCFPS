# Enable Secret Manager API
resource "google_project_service" "secretmanager" {
  service = "secretmanager.googleapis.com"
  
  disable_on_destroy = false
}

# Secret for AWS credentials
resource "google_secret_manager_secret" "aws_credentials" {
  secret_id = "${var.project_prefix}-aws-credentials"
  
  replication {
    auto {}
  }
  
  labels = {
    managed_by  = "terraform"
    project     = "multicloud-file-processor"
    environment = "prod"
  }
  
  # Need to wait for API to be enabled
  depends_on = [google_project_service.secretmanager]
}

# Initial secret version with placeholder
resource "google_secret_manager_secret_version" "aws_credentials_version" {
  secret      = google_secret_manager_secret.aws_credentials.id
  secret_data = jsonencode({
    # Placeholder data - actual credentials should be set manually or through CI/CD
    aws_access_key_id     = "placeholder",
    aws_secret_access_key = "placeholder",
    aws_region            = var.aws_region
  })
  
  lifecycle {
    ignore_changes = [secret_data]
  }
}

# Grant access to the processor service account
resource "google_secret_manager_secret_iam_binding" "aws_credentials_binding" {
  secret_id = google_secret_manager_secret.aws_credentials.secret_id
  role      = "roles/secretmanager.secretAccessor"
  
  members = [
    "serviceAccount:${google_service_account.processor_sa.email}"
  ]
} 