"""API Routes for WebUI

This package provides API endpoints for the WebUI application:
- validate_path.py: Validates cloud storage paths (s3:// and gs://)
- upload_local.py: Handles local file uploads to temporary cloud storage
- submit_task.py: Submits processing tasks to AWS SQS or GCP Pub/Sub
- task_status.py: Queries task processing status
""" 