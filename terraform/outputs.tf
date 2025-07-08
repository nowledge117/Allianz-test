output "cluster_name" {
  description = "Kubernetes cluster name"
  value       = module.eks.cluster_id
}

output "cluster_endpoint" {
  description = "Kubernetes cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "ecr_repository_url" {
  description = "The URL of the ECR repository for the application"
  value       = aws_ecr_repository.app_repo.repository_url
}

output "jenkins_iam_role_arn" {
  description = "The ARN of the IAM role for the Jenkins service account"
  value       = module.jenkins_irsa_role.iam_role_arn
}