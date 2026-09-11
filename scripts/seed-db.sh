#!/bin/bash
# ============================================================
# Database Seeding Script
# Populates development databases with sample data
# ============================================================
set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Seeding Development Databases"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Seed PostgreSQL
echo "→ Seeding PostgreSQL..."
docker compose -f docker/compose.yaml exec -T postgres psql \
    -U "${POSTGRES_USER:-app_user}" \
    -d "${POSTGRES_DB:-scalable_ai}" <<'SQL'

-- Insert sample users
INSERT INTO users (id, email, full_name, hashed_password, role, is_active)
VALUES
    (gen_random_uuid(), 'admin@example.com', 'Admin User', 'argon2hash_adminpass', 'admin', true),
    (gen_random_uuid(), 'user@example.com', 'Regular User', 'argon2hash_userpass', 'user', true),
    (gen_random_uuid(), 'dev@example.com', 'Developer', 'argon2hash_devpass', 'developer', true)
ON CONFLICT (email) DO NOTHING;

SELECT 'PostgreSQL seeded: ' || count(*) || ' users' FROM users;
SQL

# Seed MongoDB
echo "→ Seeding MongoDB..."
docker compose -f docker/compose.yaml exec -T mongo mongosh \
    --username "${MONGO_INITDB_ROOT_USERNAME:-admin}" \
    --password "${MONGO_INITDB_ROOT_PASSWORD:-password}" \
    --authenticationDatabase admin \
    "${MONGO_DB:-scalable_ai_docs}" <<'JS'

// Insert sample inference logs
db.inference_logs.insertMany([
    {
        request_id: "seed-001",
        model_name: "text-classifier-v1",
        status: "completed",
        input_data: { text: "Sample input text" },
        output_data: { predictions: [0.9, 0.08, 0.02] },
        latency_ms: 45.2,
        created_at: new Date(),
        metadata: { source: "seed" }
    },
    {
        request_id: "seed-002",
        model_name: "sentiment-analyzer-v2",
        status: "completed",
        input_data: { text: "Another sample" },
        output_data: { predictions: [0.1, 0.2, 0.7] },
        latency_ms: 38.7,
        created_at: new Date(),
        metadata: { source: "seed" }
    }
]);

print("MongoDB seeded: " + db.inference_logs.countDocuments() + " inference logs");
JS

echo ""
echo "✓ Database seeding complete!"
