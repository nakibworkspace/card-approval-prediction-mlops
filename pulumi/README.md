# Pulumi Infrastructure - AWS

This directory contains the Pulumi Infrastructure as Code (IaC) for deploying the Card Approval Prediction system on AWS.

## What Gets Deployed

1. **S3 Bucket** - For DVC data versioning, MLflow artifacts, and model storage
2. **IAM Roles** - For App Runner and EC2 instances
3. **EC2 Instance (t3.medium)** - Monitoring stack with Prometheus, Grafana, and Nginx
4. **Security Groups** - Network access control

## Prerequisites

```bash
# Install Pulumi
curl -fsSL https://get.pulumi.com | sh

# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure
```

## Deployment

```bash
# Navigate to pulumi directory
cd pulumi

# Install Python dependencies
pip install -r requirements.txt

# Login to Pulumi (use local backend or Pulumi Cloud)
pulumi login --local  # For local state management
# OR
pulumi login  # For Pulumi Cloud

# Initialize stack
pulumi stack init dev

# Preview changes
pulumi preview

# Deploy infrastructure
pulumi up

# View outputs
pulumi stack output
```

## Outputs

After deployment, you'll get:

- `s3_bucket_name` - S3 bucket for data/models
- `s3_bucket_url` - S3 URL (s3://bucket-name)
- `monitoring_instance_public_ip` - Public IP of monitoring server
- `grafana_url` - Grafana dashboard URL
- `prometheus_url` - Prometheus URL

## Access Monitoring

```bash
# Get monitoring URLs
pulumi stack output grafana_url
pulumi stack output prometheus_url

# Default Grafana credentials
# Username: admin
# Password: admin (change on first login)
```

## Destroy Infrastructure

```bash
pulumi destroy
```

## Stack Management

```bash
# List stacks
pulumi stack ls

# Switch stack
pulumi stack select prod

# Export stack state
pulumi stack export > stack-backup.json
```
