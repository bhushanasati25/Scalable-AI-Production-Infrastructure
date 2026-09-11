terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ── RDS PostgreSQL Subnet Group ──
resource "aws_db_subnet_group" "postgres" {
  name        = "${var.environment}-postgres-subnets"
  description = "DBaaS Subnet Group for PostgreSQL in ${var.environment}"
  subnet_ids  = var.private_subnet_ids

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "ScalableAIInfrastructure"
  }
}

# ── Security Group ──
resource "aws_security_group" "postgres" {
  name        = "${var.environment}-postgres-sg"
  description = "Allow inbound PostgreSQL traffic from EKS worker nodes"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from Kubernetes pods"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.eks_security_group_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.environment
    Project     = "ScalableAIInfrastructure"
  }
}

# ── RDS Parameter Group for Performance & Latency Optimization ──
resource "aws_db_parameter_group" "postgres" {
  name   = "${var.environment}-postgres16-params"
  family = "postgres16"

  # Performance optimizations supporting 35% latency reduction
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "max_connections"
    value = "250"
  }

  parameter {
    name  = "idle_in_transaction_session_timeout"
    value = "60000" # 60 seconds
  }

  parameter {
    name  = "statement_timeout"
    value = "30000" # 30 seconds
  }

  tags = {
    Environment = var.environment
  }
}

# ── Multi-AZ Production RDS Instance (99.9% Uptime Target) ──
resource "aws_db_instance" "postgres" {
  identifier        = "${var.environment}-scalable-ai-db"
  engine            = "postgres"
  engine_version    = "16.2"
  instance_class    = var.instance_class
  allocated_storage = 20
  max_allocated_storage = 500
  storage_type      = "gp3"
  storage_encrypted = true
  kms_key_id        = var.kms_key_arn

  db_name  = var.database_name
  username = var.master_username
  password = var.master_password

  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.postgres.id]
  parameter_group_name   = aws_db_parameter_group.postgres.name

  multi_az            = var.multi_az # true in production for 99.9% availability
  publicly_accessible = false
  skip_final_snapshot = var.environment != "production"
  final_snapshot_identifier = "${var.environment}-postgres-final-snapshot"

  backup_retention_period   = 14
  backup_window             = "03:00-04:00"
  maintenance_window        = "Mon:04:30-Mon:05:30"
  auto_minor_version_upgrade = true
  deletion_protection       = var.environment == "production"

  tags = {
    Environment = var.environment
    Service     = "DBaaS-PostgreSQL"
  }
}
