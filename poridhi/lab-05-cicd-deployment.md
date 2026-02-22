# Lab 05: CI/CD with GitHub Actions & EC2 Deployment

## Introduction

This lab implements complete CI/CD automation using GitHub Actions. You'll set up continuous integration (code quality, tests, security scans), continuous deployment (build, push to DockerHub, deploy to EC2), and automated health checks. The pipeline ensures only tested, secure code reaches production.

## Learning Objectives

1. Create GitHub Actions workflows for CI/CD
2. Implement automated testing and code quality checks
3. Add security scanning (CodeQL, Trivy, Bandit)
4. Build and push Docker images automatically
5. Deploy to EC2 from DockerHub
6. Implement health checks and rollback
7. Set up deployment notifications

**Prerequisites:** Completed Labs 01-04, GitHub repository, EC2 instance

**Estimated Time:** 6-8 hours

## Prologue: The Challenge

Manual deployment is error-prone:
- Forgot to run tests before deploying
- Pushed vulnerable dependencies to production
- Deployed wrong Docker image version
- No rollback when deployment fails
- Team doesn't know deployment status

You need automation that:
- Runs tests on every push
- Scans for security vulnerabilities
- Builds and tags images correctly
- Deploys to EC2 automatically
- Verifies deployment health
- Rolls back on failure
- Notifies team of status

## Environment Setup

```bash
# Create GitHub Actions directory
mkdir -p .github/workflows

# Create deployment scripts
mkdir -p scripts/deployment

# Install GitHub CLI (optional)
brew install gh  # macOS
# or
sudo apt install gh  # Linux
```

## Chapter 1: Continuous Integration Workflow

### 1.1 CI Workflow

```yaml
# .github/workflows/ci.yml
name: Continuous Integration

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  code-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install black flake8 pylint isort
          pip install -r requirements-api.txt
      
      - name: Code formatting (Black)
        run: black --check app/
      
      - name: Import sorting (isort)
        run: isort --check-only app/
      
      - name: Linting (Flake8)
        run: flake8 app/ --max-line-length=100
      
      - name: Static analysis (Pylint)
        run: pylint app/ --fail-under=8.0
  
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Bandit (Python security)
        run: |
          pip install bandit
          bandit -r app/ -f json -o bandit-report.json
      
      - name: Run Safety (dependency check)
        run: |
          pip install safety
          safety check --json
      
      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: bandit-report.json
  
  codeql-analysis:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Initialize CodeQL
        uses: github/codeql-action/init@v2
        with:
          languages: python
      
      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v2
  
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements-api.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests with coverage
        run: |
          pytest tests/ --cov=app --cov-report=xml --cov-report=html
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
  
  docker-build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: docker build -f Dockerfile.api -t test-image .
      
      - name: Test image
        run: |
          docker run -d --name test-container -p 8000:8000 test-image
          sleep 10
          curl -f http://localhost:8000/health || exit 1
          docker stop test-container
      
      - name: Scan image with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: test-image
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

**CI Pipeline Stages:**
1. **Code Quality**: Black, isort, Flake8, Pylint
2. **Security**: Bandit, Safety, CodeQL
3. **Tests**: Unit tests with coverage
4. **Docker**: Build and scan image

## Chapter 2: Continuous Deployment Workflow

### 2.1 CD Workflow

```yaml
# .github/workflows/cd.yml
name: Continuous Deployment

on:
  push:
    branches: [main]
    tags:
      - 'v*'

env:
  DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
  IMAGE_NAME: card-approval-api

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to DockerHub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile.api
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=${{ env.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=${{ env.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}:buildcache,mode=max
  
  deploy-to-ec2:
    runs-on: ubuntu-latest
    needs: build-and-push
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy to EC2
        env:
          EC2_HOST: ${{ secrets.EC2_HOST }}
          EC2_USER: ${{ secrets.EC2_USER }}
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
        run: |
          # Setup SSH
          mkdir -p ~/.ssh
          echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H $EC2_HOST >> ~/.ssh/known_hosts
          
          # Copy deployment files
          scp docker-compose.api.yml $EC2_USER@$EC2_HOST:~/
          scp scripts/deployment/deploy.sh $EC2_USER@$EC2_HOST:~/
          
          # Execute deployment
          ssh $EC2_USER@$EC2_HOST "bash ~/deploy.sh"
      
      - name: Health check
        run: |
          sleep 30
          curl -f http://${{ secrets.EC2_HOST }}/health || exit 1
      
      - name: Rollback on failure
        if: failure()
        run: |
          ssh $EC2_USER@$EC2_HOST "bash ~/rollback.sh"
  
  notify:
    runs-on: ubuntu-latest
    needs: [build-and-push, deploy-to-ec2]
    if: always()
    steps:
      - name: Send Slack notification
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
          payload: |
            {
              "text": "Deployment ${{ job.status }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Deployment Status:* ${{ job.status }}\n*Branch:* ${{ github.ref }}\n*Commit:* ${{ github.sha }}"
                  }
                }
              ]
            }
```

**CD Pipeline Stages:**
1. **Build & Push**: Build image, push to DockerHub
2. **Deploy**: SSH to EC2, pull image, restart services
3. **Health Check**: Verify deployment
4. **Notify**: Send status to Slack

## Chapter 3: Deployment Scripts

### 3.1 Deployment Script

```bash
# scripts/deployment/deploy.sh
#!/bin/bash
set -e

echo "========================================="
echo "Starting Deployment"
echo "========================================="

# Configuration
IMAGE_NAME="yourusername/card-approval-api:latest"
COMPOSE_FILE="docker-compose.api.yml"
BACKUP_DIR="$HOME/backups"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup current state
echo "Creating backup..."
BACKUP_FILE="$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).tar.gz"
docker-compose -f $COMPOSE_FILE ps -q | xargs docker inspect > $BACKUP_DIR/containers.json
tar -czf $BACKUP_FILE docker-compose.api.yml .env

# Pull latest image
echo "Pulling latest image..."
docker pull $IMAGE_NAME

# Stop current services
echo "Stopping services..."
docker-compose -f $COMPOSE_FILE down

# Start new services
echo "Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services
echo "Waiting for services to be ready..."
sleep 30

# Health check
echo "Performing health check..."
if curl -f http://localhost:8000/health; then
    echo "✓ Deployment successful"
    
    # Cleanup old images
    docker image prune -f
    
    # Keep only last 5 backups
    ls -t $BACKUP_DIR/backup-*.tar.gz | tail -n +6 | xargs -r rm
else
    echo "✗ Health check failed"
    echo "Rolling back..."
    bash ~/rollback.sh
    exit 1
fi

echo "========================================="
echo "Deployment Complete"
echo "========================================="
```

### 3.2 Rollback Script

```bash
# scripts/deployment/rollback.sh
#!/bin/bash
set -e

echo "========================================="
echo "Starting Rollback"
echo "========================================="

BACKUP_DIR="$HOME/backups"
COMPOSE_FILE="docker-compose.api.yml"

# Find latest backup
LATEST_BACKUP=$(ls -t $BACKUP_DIR/backup-*.tar.gz | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "✗ No backup found"
    exit 1
fi

echo "Restoring from: $LATEST_BACKUP"

# Stop current services
docker-compose -f $COMPOSE_FILE down

# Restore backup
tar -xzf $LATEST_BACKUP

# Start services
docker-compose -f $COMPOSE_FILE up -d

# Wait and check
sleep 30
if curl -f http://localhost:8000/health; then
    echo "✓ Rollback successful"
else
    echo "✗ Rollback failed - manual intervention required"
    exit 1
fi

echo "========================================="
echo "Rollback Complete"
echo "========================================="
```

### 3.3 Health Check Script

```bash
# scripts/deployment/health-check.sh
#!/bin/bash

MAX_RETRIES=10
RETRY_DELAY=5

for i in $(seq 1 $MAX_RETRIES); do
    echo "Health check attempt $i/$MAX_RETRIES..."
    
    if curl -f http://localhost:8000/health && \
       curl -f http://localhost:8000/health/ready; then
        echo "✓ Service is healthy"
        exit 0
    fi
    
    if [ $i -lt $MAX_RETRIES ]; then
        echo "Retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    fi
done

echo "✗ Health check failed after $MAX_RETRIES attempts"
exit 1
```

## Chapter 4: EC2 Setup with Pulumi

### 4.1 EC2 Infrastructure

```python
# pulumi/ec2.py
"""EC2 instance for deployment."""

import pulumi
import pulumi_aws as aws

def create_ec2_instance(vpc_id: str, subnet_id: str, security_group_id: str, iam_role: str):
    """Create EC2 instance for API deployment."""
    
    # Instance profile
    instance_profile = aws.iam.InstanceProfile(
        "mlops-instance-profile",
        role=iam_role
    )
    
    # EC2 instance
    instance = aws.ec2.Instance(
        "mlops-api-server",
        instance_type="t3.medium",
        ami="ami-0c55b159cbfafe1f0",  # Ubuntu 22.04 LTS
        subnet_id=subnet_id,
        vpc_security_group_ids=[security_group_id],
        iam_instance_profile=instance_profile.name,
        user_data="""#!/bin/bash
            # Install Docker
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            usermod -aG docker ubuntu
            
            # Install Docker Compose
            curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            chmod +x /usr/local/bin/docker-compose
            
            # Install AWS CLI
            apt-get update
            apt-get install -y awscli
        """,
        tags={
            "Name": "MLOps API Server",
            "Environment": "production"
        }
    )
    
    # Elastic IP
    eip = aws.ec2.Eip(
        "mlops-api-eip",
        instance=instance.id,
        tags={"Name": "MLOps API EIP"}
    )
    
    return {"instance": instance, "eip": eip}
```

### 4.2 Security Group

```python
# pulumi/security_group.py
"""Security group for EC2."""

import pulumi_aws as aws

def create_security_group(vpc_id: str):
    """Create security group for API server."""
    
    sg = aws.ec2.SecurityGroup(
        "mlops-api-sg",
        vpc_id=vpc_id,
        description="Security group for MLOps API",
        ingress=[
            # SSH
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=22,
                to_port=22,
                cidr_blocks=["0.0.0.0/0"]
            ),
            # HTTP
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=80,
                to_port=80,
                cidr_blocks=["0.0.0.0/0"]
            ),
            # HTTPS
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=443,
                to_port=443,
                cidr_blocks=["0.0.0.0/0"]
            ),
            # API
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=8000,
                to_port=8000,
                cidr_blocks=["0.0.0.0/0"]
            )
        ],
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"]
            )
        ],
        tags={"Name": "MLOps API Security Group"}
    )
    
    return sg
```

## Chapter 5: GitHub Secrets Configuration

### 5.1 Required Secrets

Set these in GitHub repository settings (Settings → Secrets and variables → Actions):

```bash
# DockerHub
DOCKERHUB_USERNAME=your_username
DOCKERHUB_TOKEN=your_token

# AWS
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# EC2
EC2_HOST=your_ec2_ip
EC2_USER=ubuntu
SSH_PRIVATE_KEY=your_private_key

# Notifications
SLACK_WEBHOOK_URL=your_webhook_url
```

### 5.2 Setting Secrets via CLI

```bash
# Using GitHub CLI
gh secret set DOCKERHUB_USERNAME -b"your_username"
gh secret set DOCKERHUB_TOKEN -b"your_token"
gh secret set AWS_ACCESS_KEY_ID -b"your_key"
gh secret set AWS_SECRET_ACCESS_KEY -b"your_secret"
gh secret set EC2_HOST -b"your_ec2_ip"
gh secret set EC2_USER -b"ubuntu"
gh secret set SSH_PRIVATE_KEY < ~/.ssh/id_rsa
gh secret set SLACK_WEBHOOK_URL -b"your_webhook"
```

## Epilogue: Complete CI/CD Pipeline

You now have:

✅ **Automated Testing**: Every push runs tests
✅ **Security Scanning**: CodeQL, Trivy, Bandit
✅ **Automated Builds**: Docker images built and pushed
✅ **Automated Deployment**: Deploy to EC2 on merge
✅ **Health Checks**: Verify deployment success
✅ **Rollback**: Automatic rollback on failure
✅ **Notifications**: Team notified of status

**Deployment Flow:**
```
1. Developer pushes to main
2. CI runs (tests, security, quality)
3. If CI passes, build Docker image
4. Push image to DockerHub
5. SSH to EC2
6. Pull latest image
7. Restart services
8. Health check
9. If healthy: Success
   If unhealthy: Rollback
10. Notify team
```

## The Principles

1. **Automate Everything** — No manual deployments
2. **Test Before Deploy** — CI must pass
3. **Security First** — Scan code and images
4. **Fail Fast** — Detect issues early
5. **Rollback Capability** — Always have escape hatch
6. **Observability** — Know deployment status
7. **Incremental Rollout** — Deploy to staging first

## Troubleshooting

**CI Failing:**
```bash
# Run locally
black --check app/
flake8 app/
pytest tests/
```

**Deployment Failing:**
```bash
# SSH to EC2
ssh ubuntu@your-ec2-ip

# Check logs
docker-compose logs api

# Manual rollback
bash ~/rollback.sh
```

**Health Check Failing:**
```bash
# Check service status
docker-compose ps

# Check API logs
docker-compose logs api

# Test locally
curl http://localhost:8000/health
```

## Next Steps

**Enhancements:**
- Blue-green deployment
- Canary releases
- Multi-region deployment
- Kubernetes migration
- GitOps with ArgoCD

---

**🎉 Lab 05 Complete! Full MLOps Pipeline Achieved!**

## Complete System Overview

You've built a production-grade MLOps pipeline:

**Lab 01**: Automated training with Airflow & MLflow
**Lab 02**: FastAPI serving with caching
**Lab 03**: Full observability stack
**Lab 04**: Cloud infrastructure & production images
**Lab 05**: CI/CD automation

**The Complete Flow:**
```
1. Data Scientist pushes code
2. GitHub Actions runs CI
3. If tests pass, build Docker image
4. Push to DockerHub
5. Deploy to EC2
6. Health check
7. Airflow trains models weekly
8. MLflow tracks experiments
9. Best model promoted to Production
10. API loads model from MLflow
11. Predictions served with caching
12. Prometheus collects metrics
13. Grafana visualizes everything
14. Loki aggregates logs
15. Tempo traces requests
```

**Congratulations! You've mastered MLOps!** 🚀
