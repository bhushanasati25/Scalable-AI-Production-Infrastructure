#!/bin/bash
# ============================================================
# MongoDB Initialization Script
# Runs once on first container start via /docker-entrypoint-initdb.d/
# ============================================================
set -euo pipefail

echo "==> Initializing MongoDB for Scalable AI Infrastructure..."

mongosh --username "$MONGO_INITDB_ROOT_USERNAME" \
        --password "$MONGO_INITDB_ROOT_PASSWORD" \
        --authenticationDatabase admin <<EOF

// Switch to application database
use ${MONGO_DB:-scalable_ai_docs};

// Create application user with readWrite role
db.createUser({
    user: "${MONGO_APP_USER:-app_user}",
    pwd: "${MONGO_APP_PASSWORD:-app_password}",
    roles: [
        { role: "readWrite", db: "${MONGO_DB:-scalable_ai_docs}" }
    ]
});

// --- Collections with Validation Schemas ---

// Inference logs collection
db.createCollection("inference_logs", {
    validator: {
        \$jsonSchema: {
            bsonType: "object",
            required: ["request_id", "model_name", "status", "created_at"],
            properties: {
                request_id: { bsonType: "string", description: "Unique request identifier" },
                model_name: { bsonType: "string", description: "Model used for inference" },
                status: { enum: ["pending", "processing", "completed", "failed"] },
                input_data: { bsonType: "object" },
                output_data: { bsonType: "object" },
                latency_ms: { bsonType: "double" },
                created_at: { bsonType: "date" },
                metadata: { bsonType: "object" }
            }
        }
    }
});

// Audit trail collection
db.createCollection("audit_trail", {
    validator: {
        \$jsonSchema: {
            bsonType: "object",
            required: ["action", "actor", "timestamp"],
            properties: {
                action: { bsonType: "string" },
                actor: { bsonType: "string" },
                resource: { bsonType: "string" },
                details: { bsonType: "object" },
                ip_address: { bsonType: "string" },
                timestamp: { bsonType: "date" }
            }
        }
    }
});

// System metrics collection
db.createCollection("system_metrics");

// --- Indexes ---

// Inference logs indexes
db.inference_logs.createIndex({ "request_id": 1 }, { unique: true });
db.inference_logs.createIndex({ "model_name": 1, "created_at": -1 });
db.inference_logs.createIndex({ "status": 1 });
db.inference_logs.createIndex(
    { "created_at": 1 },
    { expireAfterSeconds: 7776000, name: "ttl_90_days" }  // 90-day TTL
);

// Audit trail indexes
db.audit_trail.createIndex({ "actor": 1, "timestamp": -1 });
db.audit_trail.createIndex({ "action": 1 });
db.audit_trail.createIndex(
    { "timestamp": 1 },
    { expireAfterSeconds: 31536000, name: "ttl_365_days" }  // 1-year TTL
);

// System metrics indexes
db.system_metrics.createIndex({ "metric_name": 1, "timestamp": -1 });
db.system_metrics.createIndex(
    { "timestamp": 1 },
    { expireAfterSeconds: 2592000, name: "ttl_30_days" }  // 30-day TTL
);

print("==> MongoDB initialization complete.");
EOF
