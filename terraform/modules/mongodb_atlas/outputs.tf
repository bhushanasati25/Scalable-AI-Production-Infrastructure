output "connection_string" {
  value       = mongodbatlas_advanced_cluster.cluster.connection_strings[0].standard_srv
  description = "Standard SRV connection URI for MongoDB Atlas cluster"
}

output "authenticated_mongo_url" {
  value       = "mongodb+srv://${var.db_username}:${var.db_password}@${replace(mongodbatlas_advanced_cluster.cluster.connection_strings[0].standard_srv, "mongodb+srv://", "")}/${var.database_name}?retryWrites=true&w=majority"
  sensitive   = true
  description = "Full authenticated connection string for Motor async client"
}
