terraform {
  required_version = ">= 1.5.0"
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 1.15"
    }
  }
}

# ── MongoDB Atlas 3-Node Replica Set ──
resource "mongodbatlas_advanced_cluster" "cluster" {
  project_id   = var.atlas_project_id
  name         = "${var.environment}-scalable-ai-mongo"
  cluster_type = "REPLICASET"

  replication_specs {
    region_configs {
      electable_specs {
        instance_size = var.instance_size
        node_count    = 3 # 3-node HA replica set for 99.9% uptime
      }
      provider_name = "AWS"
      region_name   = var.aws_region
      priority      = 7
    }
  }

  backup_enabled = true
  pit_enabled    = true # Point-In-Time recovery

  advanced_configuration {
    javascript_enabled = false
    minimum_tls_protocol = "TLS1_2"
  }

  tags {
    key   = "Environment"
    value = var.environment
  }
}

# ── DB User with Scoped Roles ──
resource "mongodbatlas_database_user" "app_user" {
  username           = var.db_username
  password           = var.db_password
  project_id         = var.atlas_project_id
  auth_database_name = "admin"

  roles {
    role_name     = "readWrite"
    database_name = var.database_name
  }

  scopes {
    name = mongodbatlas_advanced_cluster.cluster.name
    type = "CLUSTER"
  }
}

# ── Network IP Whitelist / Security ──
resource "mongodbatlas_project_ip_access_list" "cidr" {
  count      = length(var.allowed_cidr_blocks)
  project_id = var.atlas_project_id
  cidr_block = var.allowed_cidr_blocks[count.index]
  comment    = "Kubernetes cluster egress CIDR in ${var.environment}"
}
