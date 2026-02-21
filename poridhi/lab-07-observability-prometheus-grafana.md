# Lab 06: Observability (Prometheus & Grafana)

## Introduction

This lab implements comprehensive monitoring for your production ML system. You will instrument the API with Prometheus metrics, set up Grafana dashboards, and implement data drift detection. This enables proactive issue detection before users are affected.

## Learning Objectives

By the end of this lab, you will be able to:

1. Instrument FastAPI with Prometheus metrics
2. Set up Prometheus for metrics collection
3. Create Grafana dashboards for visualization
4. Monitor system health (latency, throughput, errors)
5. Track model performance metrics
6. Implement data drift detection with Evidently AI
7. Configure alerting rules for critical issues

**Prerequisites:** Completion of Lab 05, understanding of monitoring concepts, deployed API on AWS App Runner.

## Prologue: The Challenge

Your API is in production, serving predictions. Users report occasional slow responses, but you have no visibility into:
- How many requests per second?
- What is the average response time?
- Are predictions accurate on recent data?
- Is the input data distribution changing (drift)?

Without monitoring, you are flying blind. Issues are discovered by users, not by you. You need a monitoring system that provides real-time visibility into system health and model performance.

## Environment Setup

Install monitoring dependencies:

```bash
pip install prometheus-client evidently

# Create monitoring directory
mkdir -p monitoring/prometheus monitoring/grafana monitoring/dashboards
```

## Chapter 1: Prometheus Metrics

### 1.1 What You Will Build

You will instrument the FastAPI application with Prometheus metrics to track requests, latency, and predictions.

### 1.2 Think First: What to Monitor

**Question:** For an ML API, what metrics are most important? Consider both system and model metrics.

<details>
<summary>Click to review</summary>

**System metrics:**
- Request count (total, per endpoint)
- Request latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Active connections

**Model metrics:**
- Prediction distribution (approved vs rejected)
- Prediction confidence
- Model loading time
- Feature distribution (for drift detection)

**Business metrics:**
- Predictions per customer segment
- Approval rate trends
- High-value predictions

Start with system and model metrics. Business metrics can be added later.

</details>

### 1.3 Implementation

Create `app/core/metrics.py`:


```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# System metrics
request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_latency = Histogram(
    'api_request_duration_seconds',
    'Request latency in seconds',
    ['method', 'endpoint']
)

# Model metrics
prediction_count = Counter(
    'model_predictions_total',
    'Total predictions made',
    ['decision']
)

prediction_confidence = Histogram(
    'model_prediction_confidence',
    'Prediction confidence scores',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
)

model_load_time = Gauge(
    'model_load_duration_seconds',
    'Time taken to load model'
)

# Feature metrics for drift detection
feature_value = Histogram(
    'feature_value',
    'Feature value distribution',
    ['feature_name'],
    buckets=[0, 10000, 50000, 100000, 200000, 500000, 1000000]
)

def metrics_endpoint():
    """Expose metrics for Prometheus scraping."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

Update `app/main.py` to include metrics:

```python
from app.core.metrics import metrics_endpoint, request_count, request_latency
from fastapi import Request
import time

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to track request metrics."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_latency.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return metrics_endpoint()
```

Update `app/routers/predict.py` to track predictions:

```python
from app.core.metrics import prediction_count, prediction_confidence, feature_value

@router.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    # ... existing code ...
    
    # Track prediction metrics
    decision = "APPROVED" if result["prediction"] == 1 else "REJECTED"
    prediction_count.labels(decision=decision).inc()
    prediction_confidence.observe(result["confidence"])
    
    # Track feature values for drift detection
    feature_value.labels(feature_name="income").observe(request.AMT_INCOME_TOTAL)
    feature_value.labels(feature_name="age_days").observe(abs(request.DAYS_BIRTH))
    
    # ... return response ...
```

### 1.4 Understanding the Code

Prometheus metric types:

| Type | Purpose | Example |
|------|---------|---------|
| Counter | Monotonically increasing value | Total requests |
| Gauge | Value that can go up or down | Active connections |
| Histogram | Distribution of values | Request latency |
| Summary | Similar to histogram with quantiles | Response time percentiles |

### 1.5 Test and Verify

Start the API and check metrics:

```bash
python app/main.py

# Make some predictions
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d @test_payload.json

# View metrics
curl http://localhost:8000/metrics
```

**Predict:** What format will the metrics be in?

<details>
<summary>Click to verify</summary>

Metrics are in Prometheus text format:
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="POST",endpoint="/api/v1/predict",status="200"} 5.0

# HELP api_request_duration_seconds Request latency in seconds
# TYPE api_request_duration_seconds histogram
api_request_duration_seconds_bucket{method="POST",endpoint="/api/v1/predict",le="0.5"} 5.0
```

This format is designed for Prometheus to scrape and store.

</details>

### 1.6 Checkpoint

**Self-Assessment:**
- [ ] Metrics endpoint returns Prometheus format
- [ ] Request metrics are tracked correctly
- [ ] Prediction metrics increment with each prediction
- [ ] You understand different metric types

## Chapter 2: Prometheus Setup

### 2.1 What You Will Build

You will set up Prometheus to scrape metrics from your API and store them for querying.

### 2.2 Implementation

Create `monitoring/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'card-approval-api'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
```

Create `docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
```

Start monitoring stack:

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2.3 Test and Verify

Access Prometheus UI:

```bash
open http://localhost:9090
```

Query metrics:
- `api_requests_total`
- `rate(api_requests_total[5m])`
- `histogram_quantile(0.95, api_request_duration_seconds_bucket)`

### 2.4 Checkpoint

**Self-Assessment:**
- [ ] Prometheus is running and accessible
- [ ] Prometheus is scraping metrics from API
- [ ] You can query metrics in Prometheus UI
- [ ] You understand basic PromQL queries

## Chapter 3: Grafana Dashboards

### 3.1 What You Will Build

You will create Grafana dashboards to visualize system health and model performance.

### 3.2 Implementation

Create `monitoring/grafana/provisioning/datasources/datasources.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

Create `monitoring/grafana/provisioning/dashboards/dashboards.yml`:

```yaml
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

Create dashboard JSON (simplified example):

```json
{
  "dashboard": {
    "title": "Card Approval API Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(api_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Request Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Prediction Distribution",
        "targets": [
          {
            "expr": "rate(model_predictions_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### 3.3 Test and Verify

Access Grafana:

```bash
open http://localhost:3000
# Login: admin / admin
```

Create dashboard with panels:
1. Request rate over time
2. Latency percentiles (p50, p95, p99)
3. Error rate
4. Prediction distribution
5. Model confidence distribution

### 3.4 Checkpoint

**Self-Assessment:**
- [ ] Grafana is connected to Prometheus
- [ ] Dashboard displays real-time metrics
- [ ] You can create custom panels
- [ ] Visualizations update automatically

## Chapter 4: Data Drift Detection

### 4.1 What You Will Build

You will implement data drift detection using Evidently AI to monitor if input data distribution changes over time.

### 4.2 Think First: Why Drift Matters

**Question:** Your model was trained on 2023 data. It's now 2025. Why might the model's performance degrade even if the code hasn't changed?

<details>
<summary>Click to review</summary>

**Data drift causes:**
- Economic changes (inflation affects income distribution)
- Policy changes (new lending regulations)
- Population changes (demographic shifts)
- Seasonal patterns (holiday spending)

When input data distribution changes, model predictions become less reliable. Drift detection alerts you to retrain the model with recent data.

</details>

### 4.3 Implementation

Create `app/services/drift_detection.py`:

```python
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
import pandas as pd
import numpy as np
from datetime import datetime
import json

class DriftDetector:
    def __init__(self, reference_data_path: str):
        """Initialize drift detector with reference data."""
        self.reference_data = pd.read_csv(reference_data_path)
        self.current_data = []
        
    def add_prediction(self, features: dict):
        """Add prediction to current data buffer."""
        self.current_data.append(features)
        
    def check_drift(self) -> dict:
        """Check for data drift."""
        if len(self.current_data) < 100:
            return {"drift_detected": False, "message": "Insufficient data"}
        
        current_df = pd.DataFrame(self.current_data)
        
        # Create drift report
        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=self.reference_data, current_data=current_df)
        
        # Extract results
        results = report.as_dict()
        
        # Clear buffer
        self.current_data = []
        
        return {
            "drift_detected": results["metrics"][0]["result"]["dataset_drift"],
            "drift_score": results["metrics"][0]["result"]["drift_share"],
            "timestamp": datetime.utcnow().isoformat(),
            "samples_analyzed": len(current_df)
        }

# Global drift detector
drift_detector = None

def initialize_drift_detector(reference_data_path: str):
    """Initialize global drift detector."""
    global drift_detector
    drift_detector = DriftDetector(reference_data_path)
```

Add drift endpoint to `app/routers/predict.py`:

```python
from app.services.drift_detection import drift_detector

@router.post("/drift/check")
async def check_drift():
    """Check for data drift."""
    if drift_detector is None:
        raise HTTPException(status_code=503, detail="Drift detector not initialized")
    
    result = drift_detector.check_drift()
    return result
```

### 4.4 Test and Verify

Check for drift:

```bash
# Make multiple predictions
for i in {1..150}; do
  curl -X POST http://localhost:8000/api/v1/predict \
    -H "Content-Type: application/json" \
    -d @test_payload.json
done

# Check drift
curl http://localhost:8000/api/v1/drift/check
```

### 4.5 Checkpoint

**Self-Assessment:**
- [ ] Drift detector is initialized with reference data
- [ ] Predictions are tracked for drift analysis
- [ ] Drift check endpoint returns results
- [ ] You understand when to retrain models

## Chapter 5: Alerting

### 5.1 Implementation

Create `monitoring/prometheus/alerts.yml`:

```yaml
groups:
  - name: api_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(api_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is {{ $value }} seconds"
      
      - alert: DataDriftDetected
        expr: drift_detected == 1
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Data drift detected"
          description: "Model may need retraining"
```

### 5.2 Checkpoint

**Self-Assessment:**
- [ ] Alert rules are configured
- [ ] Alerts trigger on threshold violations
- [ ] You understand alert severity levels

## Epilogue: The Complete System

You have built comprehensive observability:

| Component | Capability |
|-----------|------------|
| Prometheus | Metrics collection and storage |
| Grafana | Visualization and dashboards |
| Evidently AI | Data drift detection |
| Alerting | Proactive issue notification |

## The Principles

1. **Monitor what matters** — Focus on metrics that indicate user impact
2. **Visualize for insight** — Dashboards reveal patterns humans miss
3. **Alert on symptoms, not causes** — Alert on user-facing issues
4. **Detect drift early** — Model performance degrades before users notice
5. **Make monitoring actionable** — Every alert should have a runbook

## Troubleshooting

### Error: Prometheus cannot scrape metrics

**Solution:** Check API is accessible from Prometheus container. Use `host.docker.internal` instead of `localhost`.

### Error: Grafana shows no data

**Solution:** Verify Prometheus datasource is configured correctly and API is generating metrics.

### Error: Drift detection fails

**Solution:** Ensure reference data has the same features as current data.

## Next Steps

1. Add custom business metrics
2. Implement automated alerting (PagerDuty, Slack)
3. Create SLO/SLI dashboards
4. Add log aggregation with Loki
5. Implement distributed tracing

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Evidently AI Documentation](https://docs.evidentlyai.com/)
- [Monitoring Best Practices](https://sre.google/sre-book/monitoring-distributed-systems/)
