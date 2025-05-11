# DynamoDB Table for Task Tracking
resource "aws_dynamodb_table" "task_tracking" {
  name         = "${var.project_prefix}-task-tracking"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "task_id"

  attribute {
    name = "task_id"
    type = "S"
  }

  # Add a sort key for easier querying by status
  attribute {
    name = "status"
    type = "S"
  }
  
  # Add session_id attribute for session-based querying
  attribute {
    name = "session_id"
    type = "S"
  }

  # Global Secondary Index for querying by status
  global_secondary_index {
    name               = "StatusIndex"
    hash_key           = "status"
    projection_type    = "ALL"
    read_capacity      = 5
    write_capacity     = 5
  }
  
  # Global Secondary Index for querying by session_id
  global_secondary_index {
    name               = "SessionIdIndex"
    hash_key           = "session_id"
    projection_type    = "ALL"
    read_capacity      = 5
    write_capacity     = 5
  }

  ttl {
    attribute_name = "expiration_time"
    enabled        = true
  }
}
