# Pub/Sub topic for file processing tasks
resource "google_pubsub_topic" "file_processing_tasks" {
  name = "${var.project_prefix}-file-processing-tasks"
  
  # Enable message retention
  message_retention_duration = "604800s"  # 7 days
  
  # Labels
  labels = {
    managed_by  = "terraform"
    project     = "multicloud-file-processor"
    environment = "prod"
  }
}

# Dead Letter Topic for failed tasks
resource "google_pubsub_topic" "file_processing_dlq" {
  name = "${var.project_prefix}-file-processing-dlq"
  
  # Labels
  labels = {
    managed_by  = "terraform"
    project     = "multicloud-file-processor"
    environment = "prod"
  }
}

# Subscription to process tasks with Cloud Run
resource "google_pubsub_subscription" "task_subscription" {
  name  = "${var.project_prefix}-task-subscription"
  topic = google_pubsub_topic.file_processing_tasks.name
  
  # Acknowledge deadline (15 minutes for long running tasks)
  ack_deadline_seconds = 900
  
  # Message retention duration (7 days)
  message_retention_duration = "604800s"
  
  # Retry policy
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"  # 10 minutes
  }
  
  # Dead letter policy
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.file_processing_dlq.id
    max_delivery_attempts = 5
  }
  
  # Push to Cloud Run
  push_config {
    push_endpoint = google_cloud_run_service.processor.status[0].url
    
    # Authentication
    oidc_token {
      service_account_email = google_service_account.pubsub_sa.email
    }
    
    # Attributes passed with the message
    attributes = {
      x-goog-version = "v1"
    }
  }
  
  # Enable exactly-once delivery
  enable_exactly_once_delivery = true
  
  # Labels
  labels = {
    managed_by  = "terraform"
    project     = "multicloud-file-processor"
    environment = "prod"
  }
}

# Subscription for dead-letter queue monitoring
resource "google_pubsub_subscription" "dlq_subscription" {
  name  = "${var.project_prefix}-dlq-subscription"
  topic = google_pubsub_topic.file_processing_dlq.name
  
  # Standard pull subscription for manual processing or monitoring
  ack_deadline_seconds = 60
  
  # Keep unacknowledged messages for 14 days
  message_retention_duration = "1209600s"
  
  # Labels
  labels = {
    managed_by  = "terraform"
    project     = "multicloud-file-processor"
    environment = "prod"
  }
}
