variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, production)"
}

variable "vpc_id" {
  type        = string
  description = "Target VPC ID"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs for Multi-AZ DB subnet group"
}

variable "eks_security_group_ids" {
  type        = list(string)
  description = "Security group IDs of EKS worker nodes allowed to connect"
  default     = []
}

variable "instance_class" {
  type        = string
  default     = "db.r6g.large"
  description = "RDS instance class (memory-optimized Graviton3 for AI workloads)"
}

variable "database_name" {
  type        = string
  default     = "scalable_ai"
}

variable "master_username" {
  type        = string
  default     = "ai_admin"
}

variable "master_password" {
  type        = string
  sensitive   = true
}

variable "multi_az" {
  type        = bool
  default     = true
  description = "Enable Multi-AZ high availability"
}

variable "kms_key_arn" {
  type        = string
  default     = null
  description = "KMS Key ARN for storage encryption at rest"
}
