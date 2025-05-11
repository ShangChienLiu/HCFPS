# Google Cloud Storage buckets for the file processing system
# This file imports and extends functionality from storage.tf

# Temp bucket for file uploads
resource "google_storage_bucket" "temp_bucket" {
  name          = "${var.project_prefix}-temp-${random_id.bucket_suffix.hex}"
  location      = var.gcp_region
  storage_class = "STANDARD"
  force_destroy = true
  
  uniform_bucket_level_access = true
  
  # Auto-delete files after 7 days
  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }
  
  labels = {
    managed_by  = "terraform"
    project     = "multicloud-file-processor"
    environment = "prod"
  }
}

# Destination bucket for processed files
resource "google_storage_bucket" "destination_bucket" {
  name          = "${var.project_prefix}-output-${random_id.bucket_suffix.hex}"
  location      = var.gcp_region
  storage_class = "STANDARD"
  force_destroy = true
  
  uniform_bucket_level_access = true
  
  # Versioning for output files
  versioning {
    enabled = true
  }
  
  labels = {
    managed_by  = "terraform"
    project     = "multicloud-file-processor"
    environment = "prod"
  }
}
