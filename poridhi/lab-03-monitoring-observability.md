# Lab 03: Monitoring and Observability Stack

## Introduction

This lab adds comprehensive monitoring to your ML pipeline. You'll implement the three pillars of observability: metrics (Prometheus), logs (Loki), and traces (Tempo), visualized through Grafana dashboards. This enables proactive issue detection, performance optimization, and system health monitoring.

## Learning Objectives

1. Instrument FastAPI with Prometheus metrics
2. Create Grafana dashboards for ML monitoring
3. Implement centralized logging with Loki
4. Add distributed tracing with Tempo
5. Configure Nginx as reverse proxy
6. Monitor model performance and drift
7. Set up alerting rules

**Prerequisites:** Completed Lab 01 & 02

**Estimated Time:** 6-8 hours

## Prologue: The Challenge

Your API is in production. Everything seems fine until:
- Response times suddenly spike (why?)
- Approval rate drops from 30% to 10% (model drift?)
- API returns 500 errors (which endpoint? which request?)
- Database queries are slow (which queries?)

Without monitoring, you're flying blind. You need:
- **Metrics**: Response times, approval rates, error rates
- **Logs**: Detailed error messages, request traces
- **Traces**: Request flow across services
- **Dashboards**: Visual representation of system health

## Environment Setup

```bash
# Create monitoring directories
mkdir -p monitoring/{prometheus,grafana/{dashboards,provisioning},loki,tempo,promtail}
mkdir -p nginx

# Install monitoring dependencies
pip install prometheus-client opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi
```

## Chapter 1: Prometheus Metrics

### 1.1 Instrumenting FastAPI

Add Prometheus metrics to track API performance.

```python
# app/core/metrics.py
"""Prometheus metrics for API monitoring."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Prediction metrics
predictions_total = Counter(
    'predictions_total',
    'Total predictions made',
    ['decision', 'model_version']
)

prediction_probability = Histogram(
    'prediction_probability',
    'Prediction probability distribution',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Model metrics
model_loaded = Gauge(
    'model_loaded',
    'Whether model is loaded (1=yes, 0=no)'
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits'
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses'
)

# Database metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration'
)

def metrics_endpoint():
    """Expose metrics for Prometheus scraping."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### 1.2 Middleware for Automatic Tracking

```python
# app/core/middleware.py
"""Middleware for metrics collection."""

from fastapi import Request
import time
from app.core.metrics import (
    http_requests_total,
    http_request_duration_seconds
)

async def metrics_middleware(request: Request, call_next):
    """Track request metrics."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

### 1.3 Update Prediction Endpoint

```python
# In app/routers/predict.py, add:

from app.core.metrics import (
    predictions_total,
    prediction_probability,
    cache_hits_total,
    cache_misses_total
)

# After getting cached result:
if cached_result:
    cache_hits_total.inc()
    # ... return cached

cache_misses_total.inc()

# After prediction:
predictions_total.labels(
    decision=response.decision,
    model_version=response.model_version
).inc()

prediction_probability.observe(response.probability)
```

### 1.4 Prometheus Configuration

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
  
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

## Chapter 2: Grafana Dashboards

### 2.1 Datasource Provisioning

```yaml
# monitoring/grafana/provisioning/datasources/datasources.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
  
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
  
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
```

### 2.2 ML Metrics Dashboard

```json
# monitoring/grafana/dashboards/ml-metrics.json
{
  "dashboard": {
    "title": "ML API Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(http_requests_total[5m])"
        }]
      },
      {
        "title": "Response Time (p95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "Approval Rate",
        "targets": [{
          "expr": "rate(predictions_total{decision=\"APPROVED\"}[5m]) / rate(predictions_total[5m])"
        }]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [{
          "expr": "rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))"
        }]
      },
      {
        "title": "Prediction Probability Distribution",
        "targets": [{
          "expr": "rate(prediction_probability_bucket[5m])"
        }]
      }
    ]
  }
}
```

**Key Metrics:**
- **Request Rate**: Requests per second
- **Response Time**: p50, p95, p99 latencies
- **Approval Rate**: % of approved applications (detect drift)
- **Cache Hit Rate**: Caching effectiveness
- **Error Rate**: 4xx and 5xx errors

## Chapter 3: Centralized Logging with Loki

### 3.1 Loki Configuration

```yaml
# monitoring/loki/loki-config.yml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb:
    directory: /loki/index
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
```

### 3.2 Promtail Configuration

```yaml
# monitoring/promtail/promtail-config.yml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
```

### 3.3 Structured Logging

```python
# Update app/core/logging.py
import json
import logging

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for Loki."""
    
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)
```

## Chapter 4: Distributed Tracing with Tempo

### 4.1 OpenTelemetry Setup

```python
# app/core/tracing.py
"""OpenTelemetry tracing configuration."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from app.core.config import settings

def setup_tracing(app):
    """Configure OpenTelemetry tracing."""
    
    if not settings.OTEL_ENABLED:
        return
    
    # Create tracer provider
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    
    # Configure OTLP exporter (sends to Tempo)
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_ENDPOINT,
        insecure=True
    )
    
    # Add span processor
    provider.add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
```

### 4.2 Tempo Configuration

```yaml
# monitoring/tempo/tempo-config.yml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/traces

query_frontend:
  search:
    enabled: true
```

### 4.3 Manual Tracing

```python
# Add to prediction endpoint
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@router.post("/predict")
async def predict(input_data: PredictionInput, db: AsyncSession = Depends(get_db)):
    with tracer.start_as_current_span("predict") as span:
        # Add attributes
        span.set_attribute("model.version", model_service.model_info['model_version'])
        span.set_attribute("input.age", input_data.AGE_YEARS)
        
        # Preprocessing span
        with tracer.start_as_current_span("preprocess"):
            features = preprocessing_service.preprocess(input_data)
        
        # Prediction span
        with tracer.start_as_current_span("model.predict"):
            result = await model_service.predict(features)
        
        # Database span
        with tracer.start_as_current_span("db.log_prediction"):
            # ... log to database
        
        return response
```

## Chapter 5: Nginx Reverse Proxy

### 5.1 Nginx Configuration

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }
    
    upstream mlflow {
        server mlflow:5000;
    }
    
    upstream airflow {
        server airflow-webserver:8080;
    }
    
    upstream grafana {
        server grafana:3000;
    }
    
    upstream prometheus {
        server prometheus:9090;
    }
    
    server {
        listen 80;
        
        # API
        location /api/ {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        # MLflow
        location /mlflow/ {
            proxy_pass http://mlflow/;
        }
        
        # Airflow
        location /airflow/ {
            proxy_pass http://airflow/;
        }
        
        # Grafana
        location /grafana/ {
            proxy_pass http://grafana/;
        }
        
        # Prometheus
        location /prometheus/ {
            proxy_pass http://prometheus/;
        }
        
        # Health check
        location /health {
            proxy_pass http://api/health;
        }
    }
}
```

## Chapter 6: Docker Compose for Lab 03

```yaml
# docker-compose.local.lab03.yml
version: '3.8'

services:
  # All Lab 01 & 02 services...
  
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: lab03-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - lab03-network
  
  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: lab03-grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
      GF_USERS_ALLOW_SIGN_UP: false
    ports:
      - "3000:3000"
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
      - loki
      - tempo
    networks:
      - lab03-network
  
  # Loki
  loki:
    image: grafana/loki:latest
    container_name: lab03-loki
    command: -config.file=/etc/loki/local-config.yaml
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki/loki-config.yml:/etc/loki/local-config.yaml
      - loki-data:/loki
    networks:
      - lab03-network
  
  # Promtail
  promtail:
    image: grafana/promtail:latest
    container_name: lab03-promtail
    command: -config.file=/etc/promtail/config.yml
    volumes:
      - ./monitoring/promtail/promtail-config.yml:/etc/promtail/config.yml
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/log:/var/log:ro
    depends_on:
      - loki
    networks:
      - lab03-network
  
  # Tempo
  tempo:
    image: grafana/tempo:latest
    container_name: lab03-tempo
    command: ["-config.file=/etc/tempo.yaml"]
    ports:
      - "3200:3200"
      - "4317:4317"
    volumes:
      - ./monitoring/tempo/tempo-config.yml:/etc/tempo.yaml
      - tempo-data:/tmp/tempo
    networks:
      - lab03-network
  
  # Nginx
  nginx:
    image: nginx:alpine
    container_name: lab03-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
      - mlflow
      - airflow-webserver
      - grafana
      - prometheus
    networks:
      - lab03-network

networks:
  lab03-network:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
  loki-data:
  tempo-data:
```

## Epilogue: The Complete Observability Stack

You now have full observability:

✅ **Metrics**: Prometheus tracks performance
✅ **Dashboards**: Grafana visualizes everything
✅ **Logs**: Loki aggregates logs
✅ **Traces**: Tempo shows request flow
✅ **Reverse Proxy**: Nginx routes traffic

**Access Services:**
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- API: http://localhost/api/v1/predict
- MLflow: http://localhost/mlflow
- Airflow: http://localhost/airflow

**Key Dashboards:**
1. **System Health**: CPU, memory, disk
2. **API Performance**: Response times, error rates
3. **ML Metrics**: Approval rates, probability distribution
4. **Cache Performance**: Hit rates, memory usage

## The Principles

1. **Observe Everything** — Metrics, logs, traces
2. **Visualize Clearly** — Dashboards for quick insights
3. **Alert Proactively** — Detect issues before users
4. **Trace Requests** — Understand request flow
5. **Centralize Logs** — Single place for debugging
6. **Monitor Business Metrics** — Not just technical metrics

## Troubleshooting

**Prometheus Not Scraping:**
```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Check metrics endpoint
curl http://localhost:8000/metrics
```

**Grafana No Data:**
```bash
# Check datasource
curl http://localhost:3000/api/datasources

# Test Prometheus query
curl 'http://localhost:9090/api/v1/query?query=up'
```

**Loki Not Receiving Logs:**
```bash
# Check Promtail
docker logs lab03-promtail

# Query Loki
curl 'http://localhost:3100/loki/api/v1/query?query={container="lab03-api"}'
```

## Next Steps

Lab 04 will add:
- Pulumi infrastructure as code
- DVC for data versioning
- S3 backend for MLflow
- Production Docker images
- DockerHub publishing

---

**🎉 Lab 03 Complete! Ready for Lab 04: Production & Cloud**
