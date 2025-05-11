# Enable Firestore API
resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"
  
  disable_on_destroy = false
}

# Firestore database for task tracking
resource "google_firestore_database" "task_tracking" {
  name                = "(default)"
  location_id         = var.gcp_region
  type                = "FIRESTORE_NATIVE"
  
  # Need to wait for API to be enabled
  depends_on = [google_project_service.firestore]
}

# Firestore index for querying tasks by status
resource "google_firestore_index" "tasks_by_status" {
  collection = "tasks"
  
  fields {
    field_path = "status"
    order      = "ASCENDING"
  }
  
  fields {
    field_path = "createdAt"
    order      = "DESCENDING"
  }
  
  # Need to wait for database to be created
  depends_on = [google_firestore_database.task_tracking]
} 