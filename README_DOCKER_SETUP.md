# Docker Compose Setup Guide

This project has two Docker Compose configurations:

## 1. docker-compose.yml (Production/AWS)

**Use for:** Production deployment with AWS S3 backend

**Features:**
- MLflow with S3 artifact storage
- Requires AWS credentials
- Full tracing enabled
- Production-ready configuration

**Start:**
```bash
# Ensure .env has AWS credentials
docker compose up -d
```

**Required environment variables:**
```bash
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

## 2. docker-compose.local.yml (Local Testing)

**Use for:** Local development and testing without AWS

**Features:**
- MLflow with local filesystem storage
- No AWS credentials required
- Tracing disabled by default
- Faster startup

**Start:**
```bash
docker compose -f docker-compose.local.yml up -d
```

**Minimal environment variables:**
```bash
# Just passwords, no AWS needed
POSTGRES_API_PASSWORD=api_password
POSTGRES_MLFLOW_PASSWORD=mlflow_password
POSTGRES_AIRFLOW_PASSWORD=airflow_password
REDIS_PASSWORD=redis_password
```

## Quick Comparison

| Feature | docker-compose.yml | docker-compose.local.yml |
|---------|-------------------|-------------------------|
| MLflow Storage | S3 (AWS) | Local filesystem |
| AWS Required | ✅ Yes | ❌ No |
| Tracing | Enabled | Disabled |
| Use Case | Production | Local testing |
| Startup Speed | Slower | Faster |

## Usage Examples

### Local Testing (No AWS)
```bash
# Copy minimal env
cp .env.example .env.local
# Edit .env.local with just passwords

# Start local stack
docker compose -f docker-compose.local.yml up -d

# Access services
# API: http://localhost:8000
# MLflow: http://localhost:5000
# Airflow: http://localhost:8080
```

### Production/AWS
```bash
# Copy full env
cp .env.example .env
# Edit .env with AWS credentials

# Start production stack
docker compose up -d

# MLflow artifacts stored in S3
# Full observability enabled
```

## Switching Between Configurations

### From Local to Production
```bash
# Stop local
docker compose -f docker-compose.local.yml down

# Start production
docker compose up -d
```

### From Production to Local
```bash
# Stop production
docker compose down

# Start local
docker compose -f docker-compose.local.yml up -d
```

## Port Differences

Both configurations use the same ports:
- API: 8000
- MLflow: 5000
- Airflow: 8080
- Grafana: 3001 (local) / 3000 (production)
- Prometheus: 9090
- PostgreSQL API: 5432
- PostgreSQL MLflow: 5433
- PostgreSQL Airflow: 5434
- Redis: 6379

## Data Persistence

Both configurations use Docker volumes for data persistence:
- `postgres-api-data`
- `postgres-mlflow-data`
- `postgres-airflow-data`
- `redis-data`
- `mlflow-artifacts` (local only)
- `prometheus-data`
- `grafana-data`
- `loki-data`
- `tempo-data`
- `airflow-logs`

**To reset all data:**
```bash
# Local
docker compose -f docker-compose.local.yml down -v

# Production
docker compose down -v
```

## Recommendations

1. **Development:** Use `docker-compose.local.yml`
   - Faster iteration
   - No AWS costs
   - Simpler setup

2. **Testing AWS Integration:** Use `docker-compose.yml`
   - Test S3 artifact storage
   - Verify AWS credentials
   - Test full observability

3. **CI/CD:** Use `docker-compose.yml`
   - Production-like environment
   - Full feature testing

## Troubleshooting

### MLflow "Restarting" with docker-compose.yml
- Check AWS credentials in `.env`
- Verify S3 bucket exists
- Check S3 bucket permissions

### MLflow "Restarting" with docker-compose.local.yml
- Wait 30 seconds for database initialization
- Check logs: `docker compose -f docker-compose.local.yml logs mlflow`

### API "Restarting"
- Train a model first (see QUICKSTART.md)
- API will start without model but show warning

## Next Steps

- [QUICKSTART.md](QUICKSTART.md) - 5-minute quick start
- [LOCAL.md](LOCAL.md) - Comprehensive local testing guide
- [README_AIRFLOW.md](README_AIRFLOW.md) - Airflow usage
