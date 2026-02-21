# Lab 06: Observability (Prometheus & Grafana)

This directory contains all the files and code needed for Lab 06.

## What's Included in This Lab

**From Labs 01-05:**
- Complete ML pipeline (Airflow, MLflow, DVC)
- FastAPI prediction API
- Docker containerization
- CI/CD with GitHub Actions
- AWS deployment

**New in Lab 06:**
- Prometheus metrics instrumentation
- Grafana dashboards
- Data drift detection with Evidently AI
- Alerting rules
- System and model monitoring

## Directory Structure

```
lab06/
├── dags/                           # Airflow (from Lab 01)
├── training/                       # Training (from Labs 01-03)
├── pulumi/                         # Infrastructure (from Labs 02, 05)
├── app/                           # FastAPI (from Lab 04)
│   ├── core/
│   │   └── metrics.py            # NEW: Prometheus metrics
│   ├── services/
│   │   └── drift_detection.py    # NEW: Data drift detection
│   └── ...
├── tests/                         # Tests (from Lab 04)
├── .github/                       # CI/CD (from Lab 05)
├── monitoring/                    # NEW: Monitoring stack
│   ├── prometheus/
│   │   ├── prometheus.yml        # Prometheus configuration
│   │   └── alerts.yml            # Alert rules
│   ├── grafana/
│   │   └── provisioning/
│   │       ├── datasources/      # Grafana datasources
│   │       └── dashboards/       # Dashboard provisioning
│   └── dashboards/               # Dashboard JSON files
├── docker-compose.monitoring.yml  # NEW: Monitoring services
├── Dockerfile
├── .dvc/
├── .env.example
├── requirements.txt
└── README.md
```

## Setup Instructions

See the lab guide: `poridhi/lab-07-observability-prometheus-grafana.md`

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# 3. Start API with metrics
python app/main.py

# 4. Generate some traffic
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/v1/predict \
    -H "Content-Type: application/json" \
    -d @test_payload.json
done

# 5. Access monitoring UIs
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)

# 6. Check drift
curl http://localhost:8000/api/v1/drift/check
```

## Monitoring Components

### Prometheus
- Scrapes metrics from API every 15s
- Stores time-series data
- Evaluates alert rules

### Grafana
- Visualizes Prometheus metrics
- Pre-configured dashboards
- Alert notifications

### Evidently AI
- Detects data drift
- Compares current vs reference data
- Triggers retraining alerts
