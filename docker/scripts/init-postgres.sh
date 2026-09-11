#!/bin/bash
# ============================================================
# PostgreSQL Initialization Script
# Runs once on first container start via /docker-entrypoint-initdb.d/
# ============================================================
set -euo pipefail

echo "==> Initializing PostgreSQL for Scalable AI Infrastructure..."

# Create extensions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- UUID generation
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    -- Performance statistics
    CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

    -- Trigram similarity for text search
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";

    -- Cryptographic functions
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";

    -- Create read-only replica user for analytics
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'readonly_user') THEN
            CREATE ROLE readonly_user WITH LOGIN PASSWORD 'readonly_password';
        END IF;
    END
    \$\$;

    -- Grant read-only access
    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO readonly_user;
    GRANT USAGE ON SCHEMA public TO readonly_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT SELECT ON TABLES TO readonly_user;

    -- Configure statement timeout for safety
    ALTER DATABASE ${POSTGRES_DB} SET statement_timeout = '30s';
    ALTER DATABASE ${POSTGRES_DB} SET lock_timeout = '10s';
    ALTER DATABASE ${POSTGRES_DB} SET idle_in_transaction_session_timeout = '60s';

    -- Log slow queries
    ALTER DATABASE ${POSTGRES_DB} SET log_min_duration_statement = 1000;
EOSQL

echo "==> PostgreSQL initialization complete."
