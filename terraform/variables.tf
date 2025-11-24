variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "bitacore"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "ecr_repo_name" {
  description = "ECR repository name"
  type        = string
  default     = "bitacore-backtest"
}

variable "vpc_id" {
  description = "VPC ID for ECS cluster"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for ECS tasks"
  type        = list(string)
}

variable "cpu" {
  description = "CPU units for ECS task"
  type        = number
  default     = 512
}

variable "memory" {
  description = "Memory for ECS task"
  type        = number
  default     = 1024
}