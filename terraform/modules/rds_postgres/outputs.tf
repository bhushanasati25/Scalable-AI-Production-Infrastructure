output "endpoint" {
  value       = aws_db_instance.postgres.endpoint
  description = "Connection endpoint for PostgreSQL DBaaS"
}

output "address" {
  value       = aws_db_instance.postgres.address
  description = "Database host address"
}

output "port" {
  value       = aws_db_instance.postgres.port
  description = "Database listening port"
}

output "database_url" {
  value       = "postgresql+asyncpg://${var.master_username}:${var.master_password}@${aws_db_instance.postgres.endpoint}/${var.database_name}"
  sensitive   = true
  description = "Constructed async SQLAlchemy connection string for microservices"
}
