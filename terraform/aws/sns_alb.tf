# SNS Topic for file processing tasks
resource "aws_sns_topic" "file_processing_tasks" {
  name = "${var.project_prefix}-file-processing-tasks"
}

# ACM Certificate (replace with your real domain)
resource "aws_acm_certificate" "alb_cert" {
  domain_name       = var.alb_domain_name # e.g., alb.example.com
  validation_method = "DNS"
}

# ALB
resource "aws_lb" "processor_alb" {
  name               = "${var.project_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = var.public_subnet_ids
}

# ALB Security Group
resource "aws_security_group" "alb_sg" {
  name        = "${var.project_prefix}-alb-sg"
  description = "Allow HTTPS inbound to ALB"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Target Group for Fargate
resource "aws_lb_target_group" "processor_tg" {
  name     = "${var.project_prefix}-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  target_type = "ip"
  health_check {
    path                = "/sns"
    protocol            = "HTTP"
    matcher             = "200-299"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

# ALB Listener (HTTPS)
resource "aws_lb_listener" "alb_https" {
  load_balancer_arn = aws_lb.processor_alb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate.alb_cert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.processor_tg.arn
  }
}

# SNS Subscription to ALB HTTPS endpoint
resource "aws_sns_topic_subscription" "alb_sns_sub" {
  topic_arn = aws_sns_topic.file_processing_tasks.arn
  protocol  = "https"
  endpoint  = "https://${var.alb_domain_name}/sns"
  endpoint_auto_confirms = true
} 