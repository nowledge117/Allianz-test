# terraform/main.tf

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.3"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"

  azs = slice(data.aws_availability_zones.available.names, 0, min(3, length(data.aws_availability_zones.available.names)))
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true

  tags = {
    "Terraform" = "true"
    "Project"   = "EKS-Jenkins-Demo"
  }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.16.0" 
  cluster_name    = var.cluster_name
  cluster_version = "1.28" 

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  enable_irsa = true
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = false
  eks_managed_node_group_defaults = {
    ami_type = "AL2_x86_64"
  }

  eks_managed_node_groups = {
    general_purpose = {
      name           = "node-group-gp1"
      instance_types = ["t3.medium"] 
      min_size       = 1
      max_size       = 3
      desired_size   = 2
    }
  }

  tags = {
    "Terraform" = "true"
    "Project"   = "EKS-Jenkins-Demo"
  }
}

resource "aws_eks_addon" "ebs_csi_driver" {
  cluster_name = module.eks.cluster_name
  addon_name   = "aws-ebs-csi-driver"
}

resource "aws_iam_role_policy_attachment" "ebs_csi_node_policy_attachment" {
  role       = module.eks.eks_managed_node_groups["general_purpose"].iam_role_name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}

resource "kubernetes_storage_class" "gp3" {
  metadata {
    name = "gp3" # This is the name we will use in our PVCs
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }
  storage_provisioner = "ebs.csi.aws.com" 
  volume_binding_mode = "WaitForFirstConsumer"
  reclaim_policy      = "Delete"
  allow_volume_expansion = true
  parameters = {
    type = "gp3" # Specify the EBS volume type
    fsType = "ext4"
  }
}

resource "aws_ecr_repository" "app_repo" {
  name                 = "demo-app" 
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    "Project" = "EKS-Jenkins-Demo"
  }
}

data "aws_iam_policy_document" "jenkins_ecr_policy_doc" {
  statement {
    sid = "AllowECRActions"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:GetRepositoryPolicy",
      "ecr:DescribeRepositories",
      "ecr:ListImages",
      "ecr:DescribeImages",
      "ecr:BatchGetImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage"
    ]
    resources = [aws_ecr_repository.app_repo.arn]
  }
}

resource "aws_iam_policy" "jenkins_ecr_policy" {
  name        = "Jenkins-ECR-Policy"
  description = "Allows Jenkins to push images to the demo-app ECR repository"
  policy      = data.aws_iam_policy_document.jenkins_ecr_policy_doc.json
}

module "jenkins_irsa_role" {
  source    = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version   = "5.30.0" # You can use a more recent version if available
  role_name = "jenkins-ecr-role"
  role_policy_arns = {
    ecr_policy = aws_iam_policy.jenkins_ecr_policy.arn
  }
  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["jenkins:jenkins-admin"] # Trust the specific SA in the specific namespace
    }
  }

  tags = {
    "Project" = "EKS-Jenkins-Demo"
  }
}