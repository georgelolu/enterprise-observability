# Enterprise Observability Architecture

## 1. Purpose

This project implements a containerized observability stack for a sample
Product Service. It demonstrates application health monitoring, custom
Prometheus metrics, distributed tracing with OpenTelemetry, trace storage
with Grafana Tempo, and dashboard visualization with Grafana.

This is a local portfolio lab, not a production high-availability deployment.

## 2. Architecture

```mermaid
flowchart TD
    U[Developer or Test Client] -->|HTTP :8001| A[FastAPI Product Service]
    A -->|Application metrics| P[Prometheus :9090]
    A -->|OTLP traces :4317| O[OpenTelemetry Collector]
    O -->|OTLP gRPC| T[Grafana Tempo]
    P -->|PromQL queries| G[Grafana :3000]
    T -->|Trace queries| G
    G --> D[Dashboards and Trace Exploration]
3. Components and Responsibilities
ComponentResponsibility
FastAPI Product ServiceServes product endpoints, health checks, readiness checks, and application metrics
OpenTelemetry instrumentationProduces distributed traces for supported application operations
OpenTelemetry CollectorReceives OTLP telemetry and forwards traces to Tempo
PrometheusScrapes and stores time-series metrics
GrafanaVisualizes metrics and provides trace exploration
Grafana TempoStores and serves distributed traces
Docker ComposeRuns the services together on a local Docker network

4. Telemetry Flow
Metrics
1. Prometheus scrapes the Product Service metrics endpoint.
2. The service exposes request counters and request-duration histograms.
3. Prometheus evaluates PromQL queries for request rate, response codes,
   latency percentiles, error rate, and scrape health.
4. Grafana presents the queries in the Product Service dashboard.
Traces
1. Instrumented application requests produce trace data.
2. The application exports traces using OTLP.
3. The OpenTelemetry Collector receives the telemetry.
4. The Collector batches trace data and exports it to Tempo.
5. Grafana queries Tempo so engineers can inspect individual traces and spans.
5. Local Endpoints
ServiceLocal URL
Product Servicehttp://127.0.0.1:8001
Health checkhttp://127.0.0.1:8001/health
Readiness checkhttp://127.0.0.1:8001/ready
Application metricshttp://127.0.0.1:8001/metrics/
Prometheushttp://127.0.0.1:9090
Grafanahttp://127.0.0.1:3000
Tempo HTTP APIhttp://127.0.0.1:3200
OTLP gRPC receiver127.0.0.1:4317
OTLP HTTP receiver127.0.0.1:4318

The web interfaces and published ports are bound to loopback for local use.
6. Reliability and Security Considerations
- Separate health and readiness endpoints support basic service checks.
- Prometheus metrics expose application behavior and request latency.
- Trace collection supports request-level troubleshooting.
- Docker named volumes preserve Prometheus, Grafana, and Tempo data across
  container recreation.
- Local configuration files are mounted read-only where appropriate.
- The local Grafana password is supplied through an ignored .env file.
- .env, Python virtual environments, caches, and backup files are excluded
  from version control.
7. Current Scope and Limitations
This implementation is a single-host lab. It does not provide multi-region
failover, redundant telemetry collectors, production authentication and TLS,
centralized long-term object storage, configured alert delivery, or tested
production service-level objectives.

The Tempo configuration uses local storage with a configured 24-hour block
retention period. Local persistence is not a substitute for a tested backup
and disaster recovery strategy.
8. Suggested Production Evolution
1. Deploy redundant collectors and monitoring services.
2. Configure authenticated access and TLS.
3. Use durable object storage and define retention requirements.
4. Define service-level indicators, objectives, and alerting rules.
5. Add load testing, capacity planning, and failure-injection exercises.
6. Automate deployment and validation through CI/CD.
7. Document and test backup restoration and recovery procedures.
   EOF
echo "Architecture document written."

### Step 29B — Incident response runbook

```bash
cd ~/enterprise-observability

cat > docs/runbooks/incident-response.md <<'EOF'
# Incident Response Runbook

## 1. Purpose

This runbook provides a repeatable first-response procedure for diagnosing
the local Enterprise Observability Stack.

## 2. Initial Triage

Start in the project directory:

```bash
cd ~/enterprise-observability
docker compose ps


Confirm that all five services are running:
- product-service
- otel-collector
- prometheus
- tempo
- grafana
Inspect logs for a service that is stopped, restarting, or reporting errors:
docker compose logs --tail=100 product-service
docker compose logs --tail=100 otel-collector
docker compose logs --tail=100 prometheus
docker compose logs --tail=100 tempo
docker compose logs --tail=100 grafana


3. Product Service Is Unhealthy
Check its health and readiness endpoints:
curl -i http://127.0.0.1:8001/health
curl -i http://127.0.0.1:8001/ready


Check the application logs and confirm the container is running:
docker compose ps product-service
docker compose logs --tail=100 product-service


Expected responses include HTTP success status codes and JSON indicating
that the service is healthy or ready.
4. Prometheus Shows a Target as DOWN
Open http://127.0.0.1:9090/targets and inspect the affected target's
health and last error.

Check Prometheus and application logs:
docker compose logs --tail=100 prometheus
docker compose logs --tail=100 product-service


From the host, verify that the application metrics endpoint responds:
curl -fsS http://127.0.0.1:8001/metrics/ | head


Check the scrape configuration at
observability/prometheus/prometheus.yml. Inside the Compose network,
Prometheus must use service names and container ports, not host loopback
addresses.
5. Traces Are Missing from Grafana
Check the Collector and Tempo logs:
docker compose logs --tail=100 otel-collector
docker compose logs --tail=100 tempo


Confirm that the application's OTLP endpoint points to the Collector
service on port 4317. Confirm that the Collector exports traces to
tempo:4317 and that the Tempo OTLP receiver is configured.

Generate fresh application traffic:
curl -i http://127.0.0.1:8001/products/101


Allow a short interval for telemetry to be exported, then search for
recent traces in Grafana Explore using the Tempo data source.
6. Grafana Is Unavailable
Check service status and logs:
docker compose ps grafana
docker compose logs --tail=100 grafana
curl -fsS http://127.0.0.1:3000/api/health


Confirm the local password variable exists without displaying its value:
grep -q '^GRAFANA_ADMIN_PASSWORD=.' .env \
  && echo "Password variable is present" \
  || echo "Password variable is missing or empty"


Validate Compose configuration:
docker compose config -q


7. Safe Recovery Actions
After collecting relevant logs and identifying the likely cause, restart
only the affected service when appropriate:
docker compose restart product-service


Replace product-service with the affected Compose service name if needed.
Recheck health, logs, metrics, and traces after the restart.

If a configuration change is required, validate it before recreating services:
docker compose config -q


Avoid deleting volumes or running docker compose down -v during initial
troubleshooting. Those actions can destroy stored metrics, traces, or
Grafana configuration.
8. Incident Closure
Before closing an incident, record:
- Observed symptoms and impact.
- Relevant logs and error messages.
- Root cause, if established.
- Corrective action and any configuration changes.
- Health-check results after recovery.
- Evidence that metrics and traces are flowing again.
- Follow-up actions to prevent recurrence.
9. Scope
This runbook is designed for the local portfolio environment. Production
incident response requires organization-specific escalation paths, alerting,
access controls, backup policies, and recovery objectives.
