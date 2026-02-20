# AWS Setup & Configuration Guide

Complete guide to setup and configure the Card Approval Prediction MLOps project on AWS.

## Prerequisites

### Required Tools:
- AWS Account with billing enabled
- `aws` CLI installed and configured
- `pulumi` CLI installed
- `docker` installed
- `dvc` installed
- `python` 3.11+
- `git` installed

### Verify Installation

```bash
# Check all tools are installed
aws --version
pulumi version
docker --version
dvc version
python --version
git --version
```

### AWS Account Setup

```bash
# Configure AWS CLI
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity

# Enable required AWS services (if not already enabled)
aws s3 ls  # Test S3 access
```

---

## Configuration Reference

### AWS Resources

| Resource | Value | Description |
|----------|-------|-------------|
| **AWS Region** | `us-east-1` | Primary region |
| **S3 Bucket** | `card-approval-prediction-data-production` | Data lake, DVC, MLflow artifacts |
| **App Runner Service** | `card-approval-api` | Serverless API deployment |
| **EC2 Instance** | `t3.medium` | Monitoring stack (Prometheus + Grafana) |
| **Docker Registry** | Docker Hub | Container image storage |

### Key Configuration Files

| File | Purpose |
|------|---------|
| `config-aws.env` | AWS credentials and settings |
| `pulumi/Pulumi.yaml` | Pulumi project configuration |
| `.dvc/config` | DVC S3 remote configuration |
| `.github/workflows/ci.yml` | CI pipeline |
| `.github/workflows/cd.yml` | CD pipeline |

---

## Step 1: Clone & Configure

```bash
git clone <your-repo-url>
cd card-approval-prediction

# Copy and edit configuration files
cp config-aws.env .env
# Edit .env: Set AWS credentials, S3 bucket name, etc.
```

**Key variables to configure in `.env`:**
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
S3_BUCKET_NAME=card-approval-prediction-data-production

MLFLOW_TRACKING_URI=http://your-mlflow-server:5000
MODEL_NAME=card_approval_model
MODEL_STAGE=Production

DOCKER_HUB_USERNAME=your-dockerhub-username
DOCKER_HUB_TOKEN=your-dockerhub-token
```

## Step 2: Development Environment

```bash
# Install MiniConda (if not already installed)
# https://docs.conda.io/en/latest/miniconda.html

# Create virtual environment
conda create -n card-approval-aws python=3.11
conda activate card-approval-aws

# Install dependencies
pip install -r requirements.txt

# Setup pre-commit hooks
pre-commit install
```

---

## Step 3: Deploy Infrastructure with Pulumi

```bash
cd pulumi

# Install Pulumi dependencies
pip install -r requirements.txt

# Login to Pulumi (choose one)
pulumi login --local  # For local state management
# OR
pulumi login  # For Pulumi Cloud (requires account)

# Initialize stack
pulumi stack init production

# Set AWS region
pulumi config set aws:region us-east-1

# Preview changes
pulumi preview

# Deploy infrastructure
pulumi up

# Save important outputs
export S3_BUCKET=$(pulumi stack output s3_bucket_name)
export MONITORING_IP=$(pulumi stack output monitoring_instance_public_ip)

echo "S3 Bucket: $S3_BUCKET"
echo "Monitoring IP: $MONITORING_IP"
```

**What gets deployed:**
- S3 bucket for data, DVC, and MLflow artifacts
- IAM roles for App Runner and EC2
- EC2 instance (t3.medium) with Prometheus, Grafana, and Nginx
- Security groups for network access

---

## Step 4: Setup DVC for Data Versioning

```bash
# Navigate back to project root
cd ..

# Initialize DVC (if not already done)
dvc init

# Configure S3 remote
dvc remote add -d s3storage s3://$S3_BUCKET/dvc-storage
dvc remote modify s3storage region us-east-1

# Verify DVC configuration
dvc remote list
dvc config core.remote

# Test S3 access
dvc push --dry-run
```

---

## Step 5: Setup Docker Hub

```bash
# Login to Docker Hub
docker login
# Enter your Docker Hub username and password

# Test Docker Hub access
docker pull hello-world
docker tag hello-world $DOCKER_HUB_USERNAME/test:latest
docker push $DOCKER_HUB_USERNAME/test:latest
docker rmi $DOCKER_HUB_USERNAME/test:latest
```

---

## Step 6: Configure GitHub Actions

### 1. Create GitHub Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

| Secret Name | Value | Purpose |
|-------------|-------|---------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | AWS authentication |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | AWS authentication |
| `DOCKER_HUB_USERNAME` | Your Docker Hub username | Docker Hub login |
| `DOCKER_HUB_TOKEN` | Your Docker Hub token | Docker Hub authentication |
| `MLFLOW_TRACKING_URI` | MLflow server URL | Model download |

### 2. Generate Docker Hub Token

1. Go to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Name: `github-actions`
4. Permissions: Read, Write, Delete
5. Copy the token and save as `DOCKER_HUB_TOKEN` secret

### 3. Test GitHub Actions

```bash
# Create a test branch
git checkout -b test-ci-cd

# Make a small change
echo "# Test" >> README.md

# Commit and push
git add .
git commit -m "test: trigger CI/CD"
git push origin test-ci-cd

# Create a pull request on GitHub
# GitHub Actions will automatically run CI pipeline
```

---

## Step 7: Setup MLflow (Optional - for training)

If you want to run MLflow locally for training:

```bash
# Install MLflow
pip install mlflow boto3

# Configure AWS credentials for MLflow
export AWS_ACCESS_KEY_ID=your-access-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-access-key
export AWS_DEFAULT_REGION=us-east-1

# Start MLflow server with S3 backend
mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root s3://$S3_BUCKET/mlflow-artifacts \
  --host 0.0.0.0 \
  --port 5000

# Access MLflow UI
open http://localhost:5000
```

---

## Configuration Details

### Pulumi Outputs

After deployment, get important information:

```bash
cd pulumi

# List all outputs
pulumi stack output

# Get specific outputs
pulumi stack output s3_bucket_name
pulumi stack output s3_bucket_url
pulumi stack output monitoring_instance_public_ip
pulumi stack output grafana_url
pulumi stack output prometheus_url
```

### Monitoring Access

```bash
# Get monitoring URLs
export MONITORING_IP=$(pulumi stack output monitoring_instance_public_ip)

echo "Grafana: http://$MONITORING_IP/grafana/"
echo "Prometheus: http://$MONITORING_IP/prometheus/"

# Default Grafana credentials
# Username: admin
# Password: admin (change on first login)
```

### DVC Configuration

Your `.dvc/config` should look like:

```ini
[core]
    remote = s3storage
    autostage = true

['remote "s3storage"']
    url = s3://card-approval-prediction-data-production/dvc-storage
    region = us-east-1
```

---

## Verification Checklist

After setup, verify everything is working:

- [ ] AWS CLI configured and working
- [ ] Pulumi infrastructure deployed successfully
- [ ] S3 bucket created and accessible
- [ ] EC2 monitoring instance running
- [ ] Grafana accessible at `http://<monitoring-ip>/grafana/`
- [ ] Prometheus accessible at `http://<monitoring-ip>/prometheus/`
- [ ] DVC configured with S3 remote
- [ ] Docker Hub login successful
- [ ] GitHub Actions secrets configured
- [ ] MLflow server running (if local training)

---

## Troubleshooting

### AWS CLI Issues

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check S3 access
aws s3 ls

# Reconfigure if needed
aws configure
```

### Pulumi Issues

```bash
# Check Pulumi state
pulumi stack

# View detailed logs
pulumi logs

# Refresh state
pulumi refresh

# Destroy and recreate (if needed)
pulumi destroy
pulumi up
```

### DVC Issues

```bash
# Check DVC status
dvc status

# Check remote configuration
dvc remote list

# Test S3 connection
aws s3 ls s3://$S3_BUCKET/dvc-storage/
```

### Docker Hub Issues

```bash
# Re-login to Docker Hub
docker logout
docker login

# Test push
docker pull alpine
docker tag alpine $DOCKER_HUB_USERNAME/test:latest
docker push $DOCKER_HUB_USERNAME/test:latest
```

---

## Next Steps

1. **[Pulumi Deployment](01_Pulumi_Deployment.md)** - Detailed Pulumi infrastructure guide
2. **[DVC Setup](02_DVC_Setup.md)** - Data versioning with DVC
3. **[MLflow Training](03_MLflow_Training.md)** - Train and register models
4. **[GitHub Actions](04_GitHub_Actions.md)** - CI/CD pipeline details
5. **[App Runner Deployment](05_App_Runner.md)** - Deploy API to AWS App Runner
6. **[Monitoring](06_Monitoring.md)** - Monitoring and drift detection

---

## Cost Estimation

Approximate monthly costs for this setup:

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| S3 | 10 GB storage + requests | $0.50 - $2 |
| App Runner | 1 vCPU, 2 GB RAM, minimal traffic | $10 - $30 |
| EC2 (t3.medium) | Monitoring stack | $30 - $40 |
| Data Transfer | Minimal | $1 - $5 |
| **Total** | | **$40 - $80/month** |

**Cost Optimization Tips:**
- Use App Runner auto-scaling to minimize costs during low traffic
- Stop EC2 monitoring instance when not needed
- Use S3 lifecycle policies to archive old data
- Enable S3 Intelligent-Tiering for automatic cost optimization

---

## Security Best Practices

1. **Never commit credentials** to Git
2. **Use IAM roles** instead of access keys when possible
3. **Enable MFA** on AWS account
4. **Rotate access keys** regularly
5. **Use least privilege** IAM policies
6. **Enable S3 encryption** at rest
7. **Use VPC security groups** to restrict access
8. **Enable CloudTrail** for audit logging
9. **Scan containers** with Trivy before deployment
10. **Keep dependencies updated** with Dependabot

---

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review AWS documentation
- Check Pulumi documentation
- Open an issue on GitHub
