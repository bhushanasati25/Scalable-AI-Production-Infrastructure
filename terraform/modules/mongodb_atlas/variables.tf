variable "atlas_project_id" {
  type        = string
  description = "MongoDB Atlas Project (Organization) ID"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "instance_size" {
  type        = string
  default     = "M10"
  description = "Atlas cluster tier"
}

variable "aws_region" {
  type        = string
  default     = "US_EAST_1"
}

variable "database_name" {
  type        = string
  default     = "scalable_ai_docs"
}

variable "db_username" {
  type        = string
  default     = "ai_mongo_user"
}

variable "db_password" {
  type        = string
  sensitive   = true
}

variable "allowed_cidr_blocks" {
  type        = list(string)
  default     = []
  description = "Allowed CIDR blocks for Atlas network access"
}
