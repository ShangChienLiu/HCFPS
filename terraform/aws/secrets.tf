# Secrets Manager for storing GCP service account key
resource "aws_secretsmanager_secret" "gcp_service_account_key" {
  name        = "${var.project_prefix}-gcp-service-account-key"
  description = "GCP service account key for cross-cloud file processing"
}

# Secret version with placeholder (actual value should be set manually or through CI/CD)
resource "aws_secretsmanager_secret_version" "gcp_service_account_key_value" {
  secret_id     = aws_secretsmanager_secret.gcp_service_account_key.id
  secret_string = jsonencode({
    type = "service_account",
    # Other fields will be populated later through AWS console or API
    # This is just a placeholder to create the secret
    project_id = var.gcp_project_id
  })
  
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Secret rotation (optional)
resource "aws_secretsmanager_secret_rotation" "gcp_service_account_key_rotation" {
  count               = var.enable_secret_rotation ? 1 : 0
  secret_id           = aws_secretsmanager_secret.gcp_service_account_key.id
  rotation_lambda_arn = aws_lambda_function.secret_rotation_lambda[0].arn
  
  rotation_rules {
    automatically_after_days = 90
  }
}

# Lambda function for secret rotation (optional)
resource "aws_lambda_function" "secret_rotation_lambda" {
  count         = var.enable_secret_rotation ? 1 : 0
  function_name = "${var.project_prefix}-secret-rotation"
  role          = aws_iam_role.secret_rotation_role[0].arn
  handler       = "index.handler"
  runtime       = "nodejs14.x"
  timeout       = 30
  filename      = "lambda_function_payload.zip"  # This should be created separately
  
  environment {
    variables = {
      SECRET_ARN = aws_secretsmanager_secret.gcp_service_account_key.arn
    }
  }
}

# IAM role for secret rotation Lambda (optional)
resource "aws_iam_role" "secret_rotation_role" {
  count = var.enable_secret_rotation ? 1 : 0
  name  = "${var.project_prefix}-secret-rotation-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for secret rotation Lambda (optional)
resource "aws_iam_role_policy" "secret_rotation_policy" {
  count = var.enable_secret_rotation ? 1 : 0
  name  = "${var.project_prefix}-secret-rotation-policy"
  role  = aws_iam_role.secret_rotation_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:UpdateSecretVersionStage",
          "secretsmanager:PutSecretValue",
          "secretsmanager:DescribeSecret"
        ],
        Effect   = "Allow",
        Resource = aws_secretsmanager_secret.gcp_service_account_key.arn
      },
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect   = "Allow",
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
} 