# ECR Repository for processor container image
resource "aws_ecr_repository" "processor_repo" {
  name                 = "${var.project_prefix}-processor"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
}

# Lifecycle policy to keep only the latest 5 images
resource "aws_ecr_lifecycle_policy" "processor_repo_policy" {
  repository = aws_ecr_repository.processor_repo.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1,
        description  = "Keep only the last 5 images",
        selection = {
          tagStatus   = "any",
          countType   = "imageCountMoreThan",
          countNumber = 5
        },
        action = {
          type = "expire"
        }
      }
    ]
  })
}
