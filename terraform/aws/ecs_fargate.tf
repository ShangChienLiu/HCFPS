# ECS Fargate configuration for the file processing system
# This file complements the fargate.tf implementation

# ECS Cluster Auto Scaling based on CloudWatch metrics

# Scale up policy - more precise scaling based on metrics
resource "aws_appautoscaling_policy" "ecs_policy_cpu" {
  name               = "${var.project_prefix}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Memory-based scaling policy
resource "aws_appautoscaling_policy" "ecs_policy_memory" {
  name               = "${var.project_prefix}-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Scheduled scaling for predictable workloads (optional)
resource "aws_appautoscaling_scheduled_action" "scale_down_night" {
  name               = "${var.project_prefix}-scale-down-night"
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  schedule           = "cron(0 0 * * ? *)" # Midnight UTC

  scalable_target_action {
    min_capacity = 1
    max_capacity = 2
  }
  
  # Only create if enable_scheduled_scaling is true
  count = var.enable_scheduled_scaling ? 1 : 0
}

resource "aws_appautoscaling_scheduled_action" "scale_up_morning" {
  name               = "${var.project_prefix}-scale-up-morning"
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  schedule           = "cron(0 8 * * ? *)" # 8 AM UTC

  scalable_target_action {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }
  
  # Only create if enable_scheduled_scaling is true
  count = var.enable_scheduled_scaling ? 1 : 0
}
