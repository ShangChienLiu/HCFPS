# Random suffix for globally unique bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# IAM binding for Cloud Run service account to access temp bucket
resource "google_storage_bucket_iam_binding" "temp_bucket_binding" {
  bucket = google_storage_bucket.temp_bucket.name
  role   = "roles/storage.admin"
  
  members = [
    "serviceAccount:${google_service_account.processor_sa.email}"
  ]
}

# IAM binding for Cloud Run service account to access destination bucket
resource "google_storage_bucket_iam_binding" "destination_bucket_binding" {
  bucket = google_storage_bucket.destination_bucket.name
  role   = "roles/storage.admin"
  
  members = [
    "serviceAccount:${google_service_account.processor_sa.email}"
  ]
} 