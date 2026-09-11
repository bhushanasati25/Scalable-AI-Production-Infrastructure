# Runbook — Incident Response

## Quick Reference

| Severity | Response Time | Escalation |
|:---------|:-------------|:-----------|
| P1 - Critical | 5 minutes | On-call → Team Lead → VP Eng |
| P2 - High | 15 minutes | On-call → Team Lead |
| P3 - Medium | 1 hour | Next business day |
| P4 - Low | 24 hours | Backlog |

---

## Common Incidents

### 🔴 Service Completely Down

**Symptoms**: Health checks failing, 502/503 errors, AlertManager firing `ServiceDown`

**Steps**:
1. Check which service is down:
   ```bash
   make health
   # or
   kubectl get pods -n scalable-ai-prod
   ```

2. Check container logs:
   ```bash
   make logs-api  # or logs-worker, logs-inference
   # or
   kubectl logs -n scalable-ai-prod deployment/api-service --tail=100
   ```

3. Restart the affected service:
   ```bash
   # Docker
   docker compose -f docker/compose.yaml restart api-service

   # Kubernetes
   kubectl rollout restart deployment/api-service -n scalable-ai-prod
   ```

4. If database-related, check database health:
   ```bash
   docker compose exec postgres pg_isready -U app_user
   docker compose exec mongo mongosh --eval "rs.status()"
   docker compose exec redis redis-cli ping
   ```

---

### 🟡 High Error Rate (> 5%)

**Symptoms**: `HighErrorRate` alert, increased 5xx responses in Grafana

**Steps**:
1. Check Grafana dashboard for error patterns
2. Identify the failing endpoint:
   ```bash
   # Check recent errors in logs
   docker compose logs api-service 2>&1 | grep -i error | tail -20
   ```
3. Check database connectivity:
   ```bash
   # PostgreSQL connections
   docker compose exec postgres psql -U app_user -d scalable_ai \
     -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
   ```
4. If connection pool exhaustion, restart the service

---

### 🟡 High Latency (P99 > 500ms)

**Symptoms**: `HighLatencyP99` alert

**Steps**:
1. Check Grafana latency dashboard
2. Identify slow queries:
   ```bash
   docker compose exec postgres psql -U app_user -d scalable_ai \
     -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
   ```
3. Check Redis cache hit rate:
   ```bash
   docker compose exec redis redis-cli INFO stats | grep keyspace
   ```
4. Scale up if load-related:
   ```bash
   kubectl scale deployment/api-service --replicas=5 -n scalable-ai-prod
   ```

---

### 🟡 Database Connection Pool Exhaustion

**Symptoms**: `PostgresConnectionPoolExhausted` alert, connection timeout errors

**Steps**:
1. Check active connections:
   ```bash
   docker compose exec postgres psql -U app_user -d scalable_ai \
     -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
   ```
2. Kill idle connections:
   ```bash
   docker compose exec postgres psql -U app_user -d scalable_ai \
     -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '10 minutes';"
   ```
3. Restart affected service to reset pool
4. Consider increasing `POSTGRES_MAX_CONNECTIONS` or adding PgBouncer

---

### 🔴 Celery Workers Not Processing

**Symptoms**: Tasks stuck in queue, Flower shows no active workers

**Steps**:
1. Check Flower dashboard: http://localhost:5555
2. Check worker status:
   ```bash
   docker compose exec worker-service celery -A app.worker inspect active
   docker compose exec worker-service celery -A app.worker inspect reserved
   ```
3. Check Redis broker:
   ```bash
   docker compose exec redis redis-cli -a $REDIS_PASSWORD LLEN default
   docker compose exec redis redis-cli -a $REDIS_PASSWORD LLEN inference
   ```
4. Restart workers:
   ```bash
   docker compose restart worker-service
   ```

---

### 🔴 Inference Service OOM

**Symptoms**: Container killed, `OOMKilled` in pod status

**Steps**:
1. Check container memory:
   ```bash
   docker stats sai-inference
   # or
   kubectl top pods -n scalable-ai-prod
   ```
2. Reduce batch size:
   ```bash
   # Update .env
   INFERENCE_MAX_BATCH_SIZE=16
   docker compose restart inference-service
   ```
3. Increase memory limit if needed
4. Consider model optimization (quantization, pruning)

---

## Post-Incident

After resolving any P1/P2 incident:

1. **Document** the incident in the on-call log
2. **Timeline**: Create a timeline of events
3. **Root Cause**: Identify and document root cause
4. **Action Items**: Create tickets for prevention
5. **Review**: Schedule post-mortem within 48 hours
