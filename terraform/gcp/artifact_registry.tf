# Google Cloud Artifact Registry for container images
resource "google_artifact_registry_repository" "processor_repo" {
  provider      = google
  location      = var.gcp_region
  repository_id = "${var.project_prefix}-processor"
  description   = "Docker repository for file processor container images"
  format        = "DOCKER"
}

# IAM binding to allow Cloud Run service account to pull images
resource "google_artifact_registry_repository_iam_member" "processor_sa_puller" {
  provider   = google
  location   = google_artifact_registry_repository.processor_repo.location
  repository = google_artifact_registry_repository.processor_repo.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.processor_sa.email}"
}

# Output the full repository path for use in CI/CD pipelines
output "artifact_registry_repository" {
  value       = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.processor_repo.repository_id}"
  description = "The full path to the GCP Artifact Registry repository"
}
