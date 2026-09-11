variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "vpc_id" {
  type        = string
  description = "Production VPC ID"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnets for RDS Multi-AZ deployment"
}

variable "eks_security_group_ids" {
  type        = list(string)
  description = "EKS node security groups"
}

variable "postgres_password" {
  type      = string
  sensitive = true
}

variable "atlas_project_id" {
  type = string
}

variable "mongodbatlas_public_key" {
  type = string
}

variable "mongodbatlas_private_key" {
  type      = string
  sensitive = true
}

variable "mongo_password" {
  type      = string
  sensitive = true
}

variable "nat_gateway_ips" {
  type    = list(string)
  default = []
}

variable "redis_endpoint" {
  type    = string
  default = "redis-cluster.internal"
}

variable "redis_password" {
  type      = string
  sensitive = true
}
