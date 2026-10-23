# Incident Response Runbook

## Purpose
Troubleshoot the local Enterprise Observability Stack without unnecessarily
destroying telemetry or Grafana configuration.

## 1. Check all services
Run:

    docker compose ps

Inspect logs for the affected service:

    docker compose logs --tail=100 product-service
    docker compose logs --tail=100 otel-collector
    docker compose logs --tail=100 prometheus
    docker compose logs --tail=100 tempo
    docker compose logs --tail=100 grafana

## 2. Product Service health failure
Check the health and readiness endpoints:

    curl -i http://127.0.0.1:8001/health
    curl -i http://127.0.0.1:8001/ready

Review application logs and verify the service is running.

## 3. Prometheus target is DOWN
Open http://127.0.0.1:9090/targets and inspect the target's last error.

Check the application metrics endpoint:

    curl -fsS http://127.0.0.1:8001/metrics/ | head

Review observability/prometheus/prometheus.yml. Inside Docker Compose,
Prometheus should use service names and container ports.

## 4. Traces are missing
Inspect Collector and Tempo logs:

    docker compose logs --tail=100 otel-collector
    docker compose logs --tail=100 tempo

Confirm the Product Service exports OTLP to otel-collector:4317 and that
the Collector exports traces to tempo:4317. Generate fresh traffic:

    curl -i http://127.0.0.1:8001/products/101

Wait briefly, then search recent traces in Grafana Explore using Tempo.

## 5. Grafana is unavailable
Check the service and health endpoint:

    docker compose ps grafana
    docker compose logs --tail=100 grafana
    curl -fsS http://127.0.0.1:3000/api/health

Confirm the GRAFANA_ADMIN_PASSWORD variable exists in the local .env
without printing or sharing its value.

## 6. Safe recovery
After collecting logs and identifying the likely cause, restart only the
affected service when appropriate. Example:

    docker compose restart product-service

Validate configuration after changes:

    docker compose config -q

Avoid docker compose down -v or deleting volumes during initial
troubleshooting because these actions can destroy stored telemetry or
Grafana configuration.

## 7. Incident closure
Record the symptoms, impact, relevant logs, root cause if established,
corrective actions, health-check results, and evidence that metrics and
traces are flowing again.

## Scope
This runbook covers the local portfolio lab. Production operations require
organization-specific escalation, alerting, access controls, backups, and
tested recovery objectives.
