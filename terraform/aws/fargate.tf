# ECS Cluster for Fargate tasks
resource "aws_ecs_cluster" "processor_cluster" {
  name = "${var.project_prefix}-processor-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# CloudWatch Log Group for container logs
resource "aws_cloudwatch_log_group" "processor_logs" {
  name              = "/ecs/${var.project_prefix}-processor"
  retention_in_days = 30
}

# Task Definition for the processor container
resource "aws_ecs_task_definition" "processor_task" {
  family                   = "${var.project_prefix}-processor"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.fargate_cpu
  memory                   = var.fargate_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  
  container_definitions = jsonencode([
    {
      name              = "processor"
      image             = "${aws_ecr_repository.processor_repo.repository_url}:latest"
      essential         = true
      memoryReservation = var.fargate_memory
      environment       = [
        { name = "CLOUD_PROVIDER", value = "aws" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "S3_TEMP_BUCKET", value = aws_s3_bucket.temp_bucket.bucket },
        { name = "S3_DESTINATION_BUCKET", value = aws_s3_bucket.destination_bucket.bucket },
        { name = "GCP_PROJECT_ID", value = var.gcp_project_id },
        { name = "DYNAMODB_TABLE", value = var.dynamodb_table_name }
      ]
      secrets           = [
        { 
          name      = "GCP_CREDENTIALS", 
          valueFrom = aws_secretsmanager_secret.gcp_service_account_key.arn 
        }
      ]
      logConfiguration  = {
        logDriver = "awslogs"
        options   = {
          "awslogs-group"         = aws_cloudwatch_log_group.processor_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "processor"
        }
      }
    }
  ])
}

# ECS Service with Auto Scaling
resource "aws_ecs_service" "processor_service" {
  name                               = "${var.project_prefix}-processor-service"
  cluster                            = aws_ecs_cluster.processor_cluster.id
  task_definition                    = aws_ecs_task_definition.processor_task.arn
  desired_count                      = var.min_capacity
  launch_type                        = "FARGATE"
  scheduling_strategy                = "REPLICA"
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  
  network_configuration {
    security_groups  = [aws_security_group.ecs_sg.id]
    subnets          = var.private_subnet_ids
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.processor_tg.arn
    container_name   = "processor"
    container_port   = 8080
  }
  
  lifecycle {
    ignore_changes = [desired_count]
  }
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_sg" {
  name        = "${var.project_prefix}-ecs-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
}

# Auto Scaling for ECS based on SQS queue depth
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.processor_cluster.name}/${aws_ecs_service.processor_service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Scale up policy
resource "aws_appautoscaling_policy" "scale_up" {
  name               = "${var.project_prefix}-scale-up"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  
  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = 60
    metric_aggregation_type = "Maximum"
    
    step_adjustment {
      metric_interval_lower_bound = 1
      scaling_adjustment          = 1
    }
  }
}

# Scale down policy
resource "aws_appautoscaling_policy" "scale_down" {
  name               = "${var.project_prefix}-scale-down"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  
  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = 300
    metric_aggregation_type = "Maximum"
    
    step_adjustment {
      metric_interval_upper_bound = 0
      scaling_adjustment          = -1
    }
  }
} 