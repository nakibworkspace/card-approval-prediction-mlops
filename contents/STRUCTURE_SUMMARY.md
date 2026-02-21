# Lab Contents Structure Summary

## Overview

The `contents/` directory contains 7 cumulative lab directories. Each lab builds upon the previous ones, adding new components while retaining everything from earlier labs.

## Cumulative Structure

```
Lab 01 (Base)
    ↓
Lab 02 (Lab 01 + DVC/Pulumi)
    ↓
Lab 03 (Lab 01-02 + MLflow S3)
    ↓
Lab 04 (Lab 01-03 + FastAPI/Docker)
    ↓
Lab 05 (Lab 01-04 + CI/CD)
    ↓
Lab 06 (Lab 01-05 + Monitoring)
    ↓
Lab 07 (Complete System)
```

## What Each Lab Adds

### Lab 01: Foundation
```
lab01/
├── dags/                    # Airflow DAGs
├── training/                # ML training code
│   ├── data/
│   ├── scripts/
│   ├── src/
│   └── models/
├── logs/
├── plugins/
└── requirements.txt
```

### Lab 02: + Infrastructure & Data Versioning
```
lab02/
├── [Everything from Lab 01]
├── pulumi/                  # NEW: Infrastructure as Code
│   ├── __main__.py
│   ├── Pulumi.yaml
│   └── requirements.txt
├── .dvc/                    # NEW: DVC configuration
└── .dvcignore              # NEW
```

### Lab 03: + Cloud ML
```
lab03/
├── [Everything from Lab 01-02]
├── training/scripts/
│   ├── run_training_s3.py   # NEW: S3 training
│   ├── load_model_s3.py     # NEW: S3 loading
│   └── query_mlflow.py      # NEW: MLflow queries
├── training/src/config/
│   └── mlflow_s3_config.py  # NEW: S3 config
└── .env.example             # NEW
```

### Lab 04: + API & Docker
```
lab04/
├── [Everything from Lab 01-03]
├── app/                     # NEW: FastAPI application
│   ├── routers/
│   ├── services/
│   ├── schemas/
│   ├── core/
│   ├── utils/
│   └── main.py
├── tests/                   # NEW: Test suite
├── Dockerfile               # NEW
├── .dockerignore           # NEW
└── test_payload.json       # NEW
```

### Lab 05: + CI/CD
```
lab05/
├── [Everything from Lab 01-04]
├── .github/                 # NEW: GitHub Actions
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── .gitignore              # NEW
└── pulumi/__main__.py      # UPDATED: + App Runner
```

### Lab 06: + Monitoring
```
lab06/
├── [Everything from Lab 01-05]
├── app/core/
│   └── metrics.py           # NEW: Prometheus metrics
├── app/services/
│   └── drift_detection.py   # NEW: Drift detection
├── monitoring/              # NEW: Monitoring stack
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts.yml
│   ├── grafana/
│   │   └── provisioning/
│   └── dashboards/
└── docker-compose.monitoring.yml  # NEW
```

### Lab 07: Complete System
```
lab07/
├── [Everything from Lab 01-06]
└── [Fully integrated, production-ready system]
```

## File Count by Lab

| Lab | Directories | Key Files | Total Components |
|-----|-------------|-----------|------------------|
| 01  | 8           | ~10       | Base system |
| 02  | 10          | ~15       | + 5 new |
| 03  | 10          | ~18       | + 3 new |
| 04  | 15          | ~25       | + 7 new |
| 05  | 17          | ~28       | + 3 new |
| 06  | 22          | ~35       | + 7 new |
| 07  | 22          | ~35       | Complete |

## Key Technologies by Lab

| Lab | Technologies Added |
|-----|--------------------|
| 01  | Airflow, MLflow, scikit-learn, XGBoost |
| 02  | Pulumi, DVC, AWS S3 |
| 03  | MLflow S3 integration, boto3 |
| 04  | FastAPI, Pydantic, Docker, uvicorn |
| 05  | GitHub Actions, CodeQL, Trivy, AWS App Runner |
| 06  | Prometheus, Grafana, Evidently AI |
| 07  | Full integration |

## Usage Patterns

### Pattern 1: Sequential Learning
Start with Lab 01, complete it, then move to Lab 02, etc.
```bash
cp -r contents/lab01 my-project
# Complete Lab 01
rm -rf my-project
cp -r contents/lab02 my-project
# Complete Lab 02
# ... continue
```

### Pattern 2: Jump to Specific Lab
Copy any lab directory - it contains everything needed.
```bash
cp -r contents/lab04 my-project
# You have Labs 01-04 content
```

### Pattern 3: Reference Implementation
Use Lab 07 as a complete reference while building your own.
```bash
# Your project
mkdir my-mlops-project

# Reference Lab 07 for guidance
ls contents/lab07/
```

## Dependencies Evolution

### Lab 01 Requirements
- apache-airflow
- mlflow
- pandas, numpy, scikit-learn, xgboost

### Lab 02 Adds
- pulumi, pulumi-aws
- dvc[s3]

### Lab 03 Adds
- python-dotenv

### Lab 04 Adds
- fastapi, uvicorn, pydantic
- httpx, pytest

### Lab 05 Adds
- flake8, black, pytest-cov
- bandit, safety

### Lab 06 Adds
- prometheus-client
- evidently

## Common Files Across All Labs

These files exist in all labs (from Lab 01 onwards):
- `requirements.txt` (updated in each lab)
- `README.md` (specific to each lab)
- `training/data/raw/.gitkeep`
- `training/data/processed/.gitkeep`

## Lab-Specific Files

Files that only appear in specific labs:

**Lab 02+**: `.dvc/`, `.dvcignore`, `pulumi/`
**Lab 03+**: `.env.example`, `*_s3.py` scripts
**Lab 04+**: `app/`, `Dockerfile`, `test_payload.json`
**Lab 05+**: `.github/`, `.gitignore`
**Lab 06+**: `monitoring/`, `docker-compose.monitoring.yml`

## Size Estimates

Approximate directory sizes (excluding data and models):

- Lab 01: ~50 KB (code only)
- Lab 02: ~60 KB
- Lab 03: ~70 KB
- Lab 04: ~100 KB
- Lab 05: ~110 KB
- Lab 06: ~130 KB
- Lab 07: ~150 KB

## Next Steps

1. Choose your starting lab based on your learning goals
2. Copy the lab directory to your working location
3. Follow the lab guide in `poridhi/lab-XX-*.md`
4. Complete the exercises and checkpoints
5. Move to the next lab when ready

## Support Files

Each lab includes:
- `README.md` - Lab-specific setup and quick start
- `requirements.txt` - All dependencies (cumulative)
- `.gitkeep` files - Preserve empty directories
- Example/template files - Configuration templates

## Important Notes

1. **Cumulative Nature**: Each lab contains ALL previous content
2. **Self-Contained**: Each lab can be used independently
3. **Production-Ready**: Lab 07 is deployment-ready
4. **Documented**: Each lab has comprehensive README
5. **Tested**: Structure follows best practices

## Maintenance

To update a lab:
1. Make changes in the highest lab number that needs it
2. Propagate changes to all subsequent labs
3. Update requirements.txt if dependencies change
4. Update README.md files as needed

Example: If you update Lab 03, also update Labs 04, 05, 06, and 07.
