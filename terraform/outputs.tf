output "ecr_repo_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.repo.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.cluster.name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.app.name
}

output "service_url" {
  description = "Load balancer URL"
  value       = "https://${aws_lb.this.dns_name}"
}