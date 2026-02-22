# Lab 04: Production Containerization & Cloud Infrastructure

## Introduction

This lab transitions from local development to production-ready cloud deployment. You'll use Pulumi for infrastructure as code, DVC for data versioning, configure S3 backends for MLflow, create production Docker images, and publish to DockerHub. The lab separates concerns with independent docker-compose files for training, API, and monitoring.

## Learning Objectives

1. Define AWS infrastructure with Pulumi (S3, IAM, VPC)
2. Version control datasets with DVC
3. Configure MLflow with S3 artifact storage
4. Create optimized production Docker images
5. Publish images to DockerHub
6. Separate services with multiple compose files
7. Implement security best practices

**Prerequisites:** Completed Labs 01-03, AWS account, DockerHub account

**Estimated Time:** 8-10 hours

## Prologue: The Challenge

Your local setup works perfectly, but production requires:
- **Scalability**: S3 for artifacts (not local disk)
- **Reproducibility**: DVC for data versioning
- **Separation**: Independent services (training, API, monitoring)
- **Security**: IAM roles, secrets management
- **Deployment**: DockerHub for image distribution

You need infrastructure as code, not manual AWS console clicking.

## Environment Setup

```bash
# Install tools
pip install pulumi pulumi-aws dvc[s3]
npm install -g pulumi

# Login to Pulumi (local backend)
pulumi login --local

# Configure AWS
aws configure
```

## Chapter 1: Pulumi Infrastructure

### 1.1 Project Structure

```
pulumi/
├── __main__.py          # Main infrastructure
├── s3.py                # S3 buckets
├── iam.py               # IAM roles and policies
├── vpc.py               # VPC and networking (for Lab 05)
├── Pulumi.yaml          # Project definition
├── Pulumi.dev.yaml      # Dev stack config
├── Pulumi.prod.yaml     # Prod stack config
└── requirements.txt     # Pulumi dependencies
```

### 1.2 S3 Buckets

```python
# pulumi/s3.py
"""S3 buckets for MLOps pipeline."""

import pulumi
import pulumi_aws as aws

def create_s3_buckets(project_name: str, environment: str):
    """Create S3 buckets for data, models, and artifacts."""
    
    # DVC data storage
    dvc_bucket = aws.s3.Bucket(
        f"{project_name}-dvc-{environment}",
        bucket=f"{project_name}-dvc-{environment}",
        versioning=aws.s3.BucketVersioningArgs(enabled=True),
        tags={"Environment": environment, "Purpose": "DVC"}
    )
    
    # MLflow artifacts
    mlflow_bucket = aws.s3.Bucket(
        f"{project_name}-mlflow-{environment}",
        bucket=f"{project_name}-mlflow-{environment}",
        versioning=aws.s3.BucketVersioningArgs(enabled=True),
        tags={"Environment": environment, "Purpose": "MLflow"}
    )
    
    # Training data
    training_bucket = aws.s3.Bucket(
        f"{project_name}-training-{environment}",
        bucket=f"{project_name}-training-{environment}",
        tags={"Environment": environment, "Purpose": "Training"}
    )
    
    return {
        "dvc_bucket": dvc_bucket,
        "mlflow_bucket": mlflow_bucket,
        "training_bucket": training_bucket
    }
```

### 1.3 IAM Roles

```python
# pulumi/iam.py
"""IAM roles and policies."""

import pulumi
import pulumi_aws as aws
import json

def create_iam_resources(buckets: dict):
    """Create IAM roles for services."""
    
    # Policy for S3 access
    s3_policy = aws.iam.Policy(
        "mlops-s3-policy",
        policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"{buckets['dvc_bucket'].arn}/*",
                    f"{buckets['mlflow_bucket'].arn}/*",
                    f"{buckets['training_bucket'].arn}/*",
                    buckets['dvc_bucket'].arn,
                    buckets['mlflow_bucket'].arn,
                    buckets['training_bucket'].arn
                ]
            }]
        })
    )
    
    # Role for EC2 instances (Lab 05)
    ec2_role = aws.iam.Role(
        "mlops-ec2-role",
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        })
    )
    
    # Attach policy to role
    aws.iam.RolePolicyAttachment(
        "mlops-ec2-policy-attachment",
        role=ec2_role.name,
        policy_arn=s3_policy.arn
    )
    
    return {"ec2_role": ec2_role, "s3_policy": s3_policy}
```

### 1.4 Main Infrastructure

```python
# pulumi/__main__.py
"""Main Pulumi infrastructure."""

import pulumi
from s3 import create_s3_buckets
from iam import create_iam_resources

# Configuration
config = pulumi.Config()
project_name = pulumi.get_project()
stack_name = pulumi.get_stack()
environment = config.get("environment") or stack_name

# Create S3 buckets
buckets = create_s3_buckets(project_name, environment)

# Create IAM resources
iam_resources = create_iam_resources(buckets)

# Export outputs
pulumi.export("dvc_bucket_name", buckets["dvc_bucket"].id)
pulumi.export("mlflow_bucket_name", buckets["mlflow_bucket"].id)
pulumi.export("training_bucket_name", buckets["training_bucket"].id)
pulumi.export("ec2_role_arn", iam_resources["ec2_role"].arn)
```

### 1.5 Deploy Infrastructure

```bash
cd pulumi

# Initialize stack
pulumi stack init production

# Set configuration
pulumi config set aws:region us-east-1
pulumi config set environment production

# Preview changes
pulumi preview

# Deploy
pulumi up

# Get outputs
pulumi stack output dvc_bucket_name
pulumi stack output mlflow_bucket_name
```

## Chapter 2: DVC Data Versioning

### 2.1 DVC Setup

```bash
# Initialize DVC
dvc init

# Configure S3 remote
export DVC_BUCKET=$(cd pulumi && pulumi stack output dvc_bucket_name)
dvc remote add -d s3storage s3://$DVC_BUCKET/dvc-storage
dvc remote modify s3storage region us-east-1

# Configure AWS credentials
dvc remote modify s3storage access_key_id $AWS_ACCESS_KEY_ID
dvc remote modify s3storage secret_access_key $AWS_SECRET_ACCESS_KEY
```

### 2.2 Track Data

```bash
# Add data to DVC
dvc add training/data/raw/application_record.csv

# Commit DVC file
git add training/data/raw/application_record.csv.dvc .dvc/config
git commit -m "Add dataset to DVC"

# Push data to S3
dvc push

# Pull data (on another machine)
dvc pull
```

### 2.3 DVC Pipeline

```yaml
# dvc.yaml
stages:
  preprocess:
    cmd: python training/scripts/preprocess_data.py
    deps:
      - training/data/raw/application_record.csv
      - training/scripts/preprocess_data.py
    outs:
      - training/data/processed/
  
  train:
    cmd: python training/scripts/train_models.py
    deps:
      - training/data/processed/
      - training/scripts/train_models.py
    outs:
      - training/models/
    metrics:
      - training/metrics.json:
          cache: false
```

## Chapter 3: MLflow S3 Backend

### 3.1 Update MLflow Configuration

```python
# Update training/scripts/airflow_tasks.py

import os

# MLflow with S3
MLFLOW_TRACKING_URI = "http://mlflow:5000"
MLFLOW_BUCKET = os.getenv("MLFLOW_BUCKET_NAME")
MLFLOW_ARTIFACT_ROOT = f"s3://{MLFLOW_BUCKET}/mlflow-artifacts"

def setup_mlflow():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    # Configure S3 artifact storage
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = "https://s3.amazonaws.com"
```

### 3.2 Update Docker Compose for Airflow

```yaml
# docker-compose.airflow.yml (Production)
version: '3.8'

services:
  postgres-mlflow:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: mlflow
      POSTGRES_USER: mlflow_user
      POSTGRES_PASSWORD: ${POSTGRES_MLFLOW_PASSWORD}
    volumes:
      - postgres-mlflow-data:/var/lib/postgresql/data
  
  mlflow:
    image: python:3.11-slim
    command: >
      bash -c "
      pip install mlflow psycopg2-binary boto3 &&
      mlflow server
      --backend-store-uri postgresql://mlflow_user:${POSTGRES_MLFLOW_PASSWORD}@postgres-mlflow:5432/mlflow
      --default-artifact-root s3://${MLFLOW_BUCKET_NAME}/mlflow-artifacts
      --host 0.0.0.0
      --port 5000
      "
    environment:
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      AWS_DEFAULT_REGION: ${AWS_REGION}
    ports:
      - "5000:5000"
    depends_on:
      - postgres-mlflow
  
  airflow-webserver:
    build: ./airflow
    command: webserver
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:${POSTGRES_AIRFLOW_PASSWORD}@postgres-airflow/airflow
      MLFLOW_TRACKING_URI: http://mlflow:5000
      MLFLOW_BUCKET_NAME: ${MLFLOW_BUCKET_NAME}
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
    volumes:
      - ./dags:/opt/airflow/dags
      - ./training:/opt/airflow/training
    ports:
      - "8080:8080"
  
  airflow-scheduler:
    build: ./airflow
    command: scheduler
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:${POSTGRES_AIRFLOW_PASSWORD}@postgres-airflow/airflow
      MLFLOW_TRACKING_URI: http://mlflow:5000
      MLFLOW_BUCKET_NAME: ${MLFLOW_BUCKET_NAME}
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
    volumes:
      - ./dags:/opt/airflow/dags
      - ./training:/opt/airflow/training

volumes:
  postgres-mlflow-data:
  postgres-airflow-data:
```

## Chapter 4: Production Docker Images

### 4.1 Multi-Stage API Dockerfile

```dockerfile
# Dockerfile.api (Production)
FROM python:3.11-slim as builder

WORKDIR /build

# Install dependencies
COPY requirements-api.txt .
RUN pip install --user --no-cache-dir -r requirements-api.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 Airflow Production Dockerfile

```dockerfile
# airflow/Dockerfile.prod
FROM apache/airflow:2.8.0-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements-airflow.txt .
RUN pip install --no-cache-dir -r requirements-airflow.txt

WORKDIR /opt/airflow
```

### 4.3 Build and Tag Images

```bash
# Build API image
docker build -f Dockerfile.api -t card-approval-api:1.0.0 .
docker tag card-approval-api:1.0.0 yourusername/card-approval-api:1.0.0
docker tag card-approval-api:1.0.0 yourusername/card-approval-api:latest

# Build Airflow image
docker build -f airflow/Dockerfile.prod -t card-approval-airflow:1.0.0 ./airflow
docker tag card-approval-airflow:1.0.0 yourusername/card-approval-airflow:1.0.0
docker tag card-approval-airflow:1.0.0 yourusername/card-approval-airflow:latest

# Push to DockerHub
docker login
docker push yourusername/card-approval-api:1.0.0
docker push yourusername/card-approval-api:latest
docker push yourusername/card-approval-airflow:1.0.0
docker push yourusername/card-approval-airflow:latest
```

## Chapter 5: Production Docker Compose Files

### 5.1 API Service

```yaml
# docker-compose.api.yml
version: '3.8'

services:
  postgres-api:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: card_approval_api
      POSTGRES_USER: api_user
      POSTGRES_PASSWORD: ${POSTGRES_API_PASSWORD}
    volumes:
      - postgres-api-data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
  
  api:
    image: yourusername/card-approval-api:latest
    environment:
      POSTGRES_HOST: postgres-api
      POSTGRES_PASSWORD: ${POSTGRES_API_PASSWORD}
      REDIS_HOST: redis
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      MLFLOW_TRACKING_URI: ${MLFLOW_TRACKING_URI}
      MODEL_NAME: card_approval_production
      MODEL_STAGE: Production
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres-api
      - redis

volumes:
  postgres-api-data:
  redis-data:
```

### 5.2 Monitoring Service

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
  
  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    ports:
      - "3000:3000"
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
      - loki
      - tempo
  
  loki:
    image: grafana/loki:latest
    command: -config.file=/etc/loki/local-config.yaml
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki/loki-config.yml:/etc/loki/local-config.yaml
      - loki-data:/loki
  
  tempo:
    image: grafana/tempo:latest
    command: ["-config.file=/etc/tempo.yaml"]
    ports:
      - "3200:3200"
      - "4317:4317"
    volumes:
      - ./monitoring/tempo/tempo-config.yml:/etc/tempo.yaml
      - tempo-data:/tmp/tempo

volumes:
  prometheus-data:
  grafana-data:
  loki-data:
  tempo-data:
```

## Epilogue: Production-Ready Infrastructure

You now have:

✅ **Infrastructure as Code**: Pulumi manages AWS resources
✅ **Data Versioning**: DVC tracks datasets
✅ **S3 Backend**: MLflow artifacts in S3
✅ **Production Images**: Optimized Docker images
✅ **DockerHub**: Images published and versioned
✅ **Separated Services**: Independent compose files

**Deployment Strategy:**
```bash
# On production server
docker-compose -f docker-compose.airflow.yml up -d
docker-compose -f docker-compose.api.yml up -d
docker-compose -f docker-compose.monitoring.yml up -d
```

## The Principles

1. **Infrastructure as Code** — No manual AWS console
2. **Version Everything** — Code, data, models, infrastructure
3. **Separate Concerns** — Independent services
4. **Optimize Images** — Multi-stage builds, non-root users
5. **Use Managed Storage** — S3 for artifacts, not local disk
6. **Security First** — IAM roles, secrets management

## Troubleshooting

**Pulumi Deployment Failed:**
```bash
pulumi stack --show-urns
pulumi destroy  # Clean up
pulumi up       # Retry
```

**DVC Push Failed:**
```bash
# Check AWS credentials
aws s3 ls s3://your-dvc-bucket/

# Check DVC config
dvc remote list
dvc remote modify s3storage --local access_key_id $AWS_ACCESS_KEY_ID
```

**MLflow S3 Access Denied:**
```bash
# Verify IAM permissions
aws s3 ls s3://your-mlflow-bucket/

# Check environment variables
echo $AWS_ACCESS_KEY_ID
```

## Next Steps

Lab 05 will add:
- GitHub Actions CI/CD
- EC2 deployment
- Automated testing
- Security scanning
- Deployment automation

---

**🎉 Lab 04 Complete! Ready for Lab 05: CI/CD**
