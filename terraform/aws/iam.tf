# ECS Execution Role - Allows ECS to pull container images and write logs
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.project_prefix}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Attach AWS managed policy for ECS task execution
resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow access to Secrets Manager
resource "aws_iam_role_policy" "ecs_execution_secrets_policy" {
  name = "${var.project_prefix}-ecs-secrets-policy"
  role = aws_iam_role.ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue"
        ],
        Effect   = "Allow",
        Resource = aws_secretsmanager_secret.gcp_service_account_key.arn
      }
    ]
  })
}

# ECS Task Role - Permissions for the container to access AWS services
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_prefix}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Allow access to SQS, S3, DynamoDB, CloudWatch
resource "aws_iam_role_policy" "ecs_task_service_policy" {
  name = "${var.project_prefix}-ecs-task-service-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          // SQS permissions removed
        ],
        Effect   = "Allow",
        Resource = "*"
      },
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ],
        Effect = "Allow",
        Resource = [
          aws_s3_bucket.temp_bucket.arn,
          "${aws_s3_bucket.temp_bucket.arn}/*",
          aws_s3_bucket.destination_bucket.arn,
          "${aws_s3_bucket.destination_bucket.arn}/*"
        ]
      },
      {
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ],
        Effect   = "Allow",
        Resource = var.dynamodb_table_arn
      },
      {
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect = "Allow",
        Resource = "${aws_cloudwatch_log_group.processor_logs.arn}:*"
      }
    ]
  })
}

# --- BEGIN iam_roles.tf content ---

# IAM Roles for Multi-Cloud Task System

# ECS Task Execution Role (for Fargate tasks)
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.project_prefix}-ecs-task-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role_policy.json
}

data "aws_iam_policy_document" "ecs_task_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# ECS Task Policy: S3, SQS, DynamoDB, Secrets Manager, CloudWatch Logs, ECR
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${var.project_prefix}-ecs-task-policy"
  role = aws_iam_role.ecs_task_execution_role.id
  policy = data.aws_iam_policy_document.ecs_task_policy.json
}

data "aws_iam_policy_document" "ecs_task_policy" {
  statement {
    actions = [
      "s3:GetObject", "s3:PutObject", "s3:ListBucket", "s3:DeleteObject"
    ]
    resources = [
      aws_s3_bucket.temp_bucket.arn,
      "${aws_s3_bucket.temp_bucket.arn}/*",
      aws_s3_bucket.destination_bucket.arn,
      "${aws_s3_bucket.destination_bucket.arn}/*"
    ]
  }
  statement {
    actions = [
      "sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes", "sqs:GetQueueUrl"
    ]
    resources = [
      aws_sqs_queue.file_processing_tasks_queue.arn,
      aws_sqs_queue.file_processing_dlq.arn
    ]
  }
  statement {
    actions = [
      "dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:Query", "dynamodb:Scan"
    ]
    resources = [
      var.dynamodb_table_arn,
      "${var.dynamodb_table_arn}/index/*"
    ]
  }
  statement {
    actions = ["secretsmanager:GetSecretValue"]
    resources = ["*"]
  }
  statement {
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
  statement {
    actions = ["ecr:GetAuthorizationToken", "ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage"]
    resources = ["*"]
  }
}

# Attach the ECS Task Execution Role to the AWS managed policy for ECS
resource "aws_iam_role_policy_attachment" "ecs_task_execution_attachment" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Cross-cloud access role (for future use, e.g., GCP credentials)
resource "aws_iam_role" "cross_cloud_access_role" {
  name = "${var.project_prefix}-cross-cloud-access-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "gcp_access_policy" {
  name        = "${var.project_prefix}-gcp-access-policy"
  description = "Policy for accessing GCP through stored credentials"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = ["secretsmanager:GetSecretValue"]
        Effect = "Allow"
        Resource = ["arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.project_prefix}-gcp-*"]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "gcp_access_attachment" {
  role       = aws_iam_role.cross_cloud_access_role.name
  policy_arn = aws_iam_policy.gcp_access_policy.arn
}
# --- END iam_roles.tf content --- 

# ...repeat for other roles/services as needed 