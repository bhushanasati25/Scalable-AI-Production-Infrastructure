terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 1.15"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "mongodbatlas" {
  public_key  = var.mongodbatlas_public_key
  private_key = var.mongodbatlas_private_key
}

# ── Provision RDS PostgreSQL DBaaS ──
module "postgres_dbaas" {
  source = "../../modules/rds_postgres"

  environment            = "production"
  vpc_id                 = var.vpc_id
  private_subnet_ids     = var.private_subnet_ids
  eks_security_group_ids = var.eks_security_group_ids
  instance_class         = "db.r6g.xlarge"
  database_name          = "scalable_ai"
  master_username        = "ai_prod_admin"
  master_password        = var.postgres_password
  multi_az               = true
}

# ── Provision MongoDB Atlas DBaaS ──
module "mongo_dbaas" {
  source = "../../modules/mongodb_atlas"

  environment         = "production"
  atlas_project_id    = var.atlas_project_id
  instance_size       = "M20"
  aws_region          = "US_EAST_1"
  database_name       = "scalable_ai_docs"
  db_username         = "ai_mongo_prod"
  db_password         = var.mongo_password
  allowed_cidr_blocks = var.nat_gateway_ips
}

# ── Automatically Populate Kubernetes Secret for GitOps / ArgoCD ──
resource "kubernetes_secret" "database_credentials" {
  metadata {
    name      = "database-credentials"
    namespace = "scalable-ai-prod"
  }

  data = {
    postgres-url     = module.postgres_dbaas.database_url
    mongo-url        = module.mongo_dbaas.authenticated_mongo_url
    redis-url        = "redis://:${var.redis_password}@${var.redis_endpoint}:6379/0"
    redis-broker-url = "redis://:${var.redis_password}@${var.redis_endpoint}:6379/1"
    redis-result-url = "redis://:${var.redis_password}@${var.redis_endpoint}:6379/2"
  }
}
