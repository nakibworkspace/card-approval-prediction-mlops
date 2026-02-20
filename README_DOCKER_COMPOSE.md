# Docker Compose Setup Guide

This guide explains how to run the complete Card Approval Prediction stack locally using Docker Compose.

## 🏗️ Architecture

The Docker Compose setup includes:

### Application Services
- **FastAPI API** - Credit approval prediction service
- **PostgreSQL (API)** - Stores predictions and cache
- **PostgreSQL (MLflow)** - MLflow metadata store
- **Redis** - Caching layer
- **MLflow Server** - Experiment tracking and model registry

### Monitoring Stack
- **Prometheus** - Metrics collection
- **Grafana** - Visualization dashboards
- **Loki** - Log aggregation
- **Promtail** - Log collector
- **Tempo** - Distributed tracing

## 📋 Prerequisites

- Docker Desktop installed
- Docker Compose v2.0+
- AWS credentials (for S3 access)
- At least 8GB RAM available

## 🚀 Quick Start

### 1. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set:
# - AWS credentials
# - Database passwords
# - Redis password
# - Grafana password
```

### 2. Start All Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 3. Verify Services

```bash
# API Health Check
curl http://localhost:8000/health

# Prometheus
open http://localhost:9090

# Grafana (admin/admin)
open http://localhost:3000

# MLflow
open http://localhost:5000
```

## 📊 Service Ports

| Service | Port | URL |
|---------|------|-----|
| FastAPI API | 8000 | http://localhost:8000 |
| Swagger Docs | 8000 | http://localhost:8000/docs |
| PostgreSQL (API) | 5432 | localhost:5432 |
| PostgreSQL (MLflow) | 5433 | localhost:5433 |
| Redis | 6379 | localhost:6379 |
| MLflow | 5000 | http://localhost:5000 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 |
| Loki | 3100 | http://localhost:3100 |
| Tempo | 3200 | http://localhost:3200 |

## 🔧 Service Management

### Start Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api

# Start with build
docker-compose up -d --build
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres-api
docker-compose logs -f redis
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
```

## 📊 Database Access

### PostgreSQL (API Database)

```bash
# Connect to API database
docker-compose exec postgres-api psql -U api_user -d card_approval_api

# View predictions
SELECT * FROM predictions ORDER BY created_at DESC LIMIT 10;

# Get prediction statistics
SELECT * FROM get_prediction_stats(7);
```

### PostgreSQL (MLflow Database)

```bash
# Connect to MLflow database
docker-compose exec postgres-mlflow psql -U mlflow_user -d mlflow

# View experiments
SELECT * FROM experiments;

# View runs
SELECT * FROM runs ORDER BY start_time DESC LIMIT 10;
```

### Redis

```bash
# Connect to Redis
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD}

# View all keys
KEYS *

# Get cache stats
INFO stats
```

## 📈 Monitoring

### Prometheus

Access: http://localhost:9090

**Useful Queries:**
```promql
# Request rate
rate(http_requests_total[5m])

# Average response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Prediction count
sum(predictions_total)
```

### Grafana

Access: http://localhost:3000
- Username: `admin`
- Password: (from .env file)

**Pre-configured Datasources:**
- Prometheus (metrics)
- Loki (logs)
- Tempo (traces)

### Loki (Logs)

Access via Grafana → Explore → Loki

**Example Queries:**
```logql
# API logs
{container="card-approval-api"}

# Error logs
{container="card-approval-api"} |= "ERROR"

# Prediction logs
{container="card-approval-api"} |= "prediction"
```

### Tempo (Traces)

Access via Grafana → Explore → Tempo

Search by:
- Service name: `card-approval-api`
- Operation name: `POST /api/v1/predict`
- Duration: `> 100ms`

## 🧪 Testing

### Make a Prediction

```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 5008804,
    "CODE_GENDER": "M",
    "FLAG_OWN_CAR": "Y",
    "FLAG_OWN_REALTY": "Y",
    "CNT_CHILDREN": 0,
    "AMT_INCOME_TOTAL": 180000.0,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Higher education",
    "NAME_FAMILY_STATUS": "Married",
    "NAME_HOUSING_TYPE": "House / apartment",
    "DAYS_BIRTH": -14000,
    "DAYS_EMPLOYED": -2500,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 1,
    "FLAG_EMAIL": 0,
    "OCCUPATION_TYPE": "Managers",
    "CNT_FAM_MEMBERS": 2.0
  }'
```

### Check Drift Detection

```bash
# Check drift status
curl http://localhost:8000/api/v1/drift/status

# List drift reports
curl http://localhost:8000/api/v1/drift/reports
```

### View Metrics

```bash
curl http://localhost:8000/metrics
```

## 🔍 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Check if port is already in use
lsof -i :8000  # or any other port

# Restart service
docker-compose restart <service-name>
```

### Database Connection Issues

```bash
# Check if PostgreSQL is healthy
docker-compose ps postgres-api

# Check PostgreSQL logs
docker-compose logs postgres-api

# Verify connection
docker-compose exec postgres-api pg_isready -U api_user
```

### Redis Connection Issues

```bash
# Check if Redis is healthy
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD} ping
```

### MLflow Issues

```bash
# Check MLflow logs
docker-compose logs mlflow

# Verify S3 access
docker-compose exec mlflow aws s3 ls s3://${S3_BUCKET_NAME}/
```

### Out of Memory

```bash
# Check Docker resource usage
docker stats

# Increase Docker Desktop memory limit
# Docker Desktop → Settings → Resources → Memory
```

## 🧹 Cleanup

### Remove All Containers and Volumes

```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Remove orphaned volumes
docker volume prune
```

### Clean Specific Service Data

```bash
# Remove API database data
docker volume rm card-approval-prediction_postgres-api-data

# Remove Redis data
docker volume rm card-approval-prediction_redis-data

# Remove Grafana data
docker volume rm card-approval-prediction_grafana-data
```

## 📊 Data Persistence

All data is persisted in Docker volumes:

| Volume | Purpose |
|--------|---------|
| `postgres-api-data` | API predictions and cache |
| `postgres-mlflow-data` | MLflow experiments and runs |
| `redis-data` | Redis cache |
| `prometheus-data` | Prometheus metrics |
| `grafana-data` | Grafana dashboards and settings |
| `loki-data` | Loki logs |
| `tempo-data` | Tempo traces |

## 🔐 Security Notes

1. **Change default passwords** in `.env` file
2. **Don't commit** `.env` file to Git
3. **Use strong passwords** for production
4. **Limit network exposure** in production
5. **Enable SSL/TLS** for production deployments

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)

## 🆘 Support

For issues:
1. Check service logs: `docker-compose logs <service>`
2. Verify environment variables in `.env`
3. Check Docker Desktop resources
4. Review this documentation
5. Open GitHub issue with logs
