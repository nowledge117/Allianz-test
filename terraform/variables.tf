variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "us-west-1"
}

variable "cluster_name" {
  description = "The name for the EKS cluster."
  type        = string
  default     = "my-demo-cluster"
}