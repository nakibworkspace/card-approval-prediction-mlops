"""
Pulumi Infrastructure as Code for Card Approval Prediction on AWS

This replaces the Terraform/GCP setup with AWS services:
- S3 for data lake, DVC storage, and MLflow artifacts
- App Runner for FastAPI prediction service
- EC2 for Monitoring Stack (Prometheus + Grafana)
"""

import pulumi
import pulumi_aws as aws
from pulumi import Config, export

# Configuration
config = Config()
project_name = "card-approval-prediction"
environment = config.get("environment") or "production"
aws_region = config.get("region") or "us-east-1"

# Tags for all resources
common_tags = {
    "Project": project_name,
    "Environment": environment,
    "ManagedBy": "Pulumi",
}

# ============================================
# S3 Buckets
# ============================================

# Main data bucket for DVC, MLflow artifacts, and datasets
data_bucket = aws.s3.Bucket(
    "card-approval-data-bucket",
    bucket=f"{project_name}-data-{environment}",
    acl="private",
    versioning=aws.s3.BucketVersioningArgs(
        enabled=True,
    ),
    lifecycle_rules=[
        aws.s3.BucketLifecycleRuleArgs(
            enabled=True,
            expiration=aws.s3.BucketLifecycleRuleExpirationArgs(
                days=90,
            ),
            noncurrent_version_expiration=aws.s3.BucketLifecycleRuleNoncurrentVersionExpirationArgs(
                days=30,
            ),
        )
    ],
    tags={**common_tags, "Purpose": "DataLake-DVC-MLflow"},
)

# Block public access
data_bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
    "data-bucket-public-access-block",
    bucket=data_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# ============================================
# IAM Roles and Policies
# ============================================

# IAM Role for App Runner to access S3 and MLflow
app_runner_role = aws.iam.Role(
    "app-runner-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "tasks.apprunner.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    }""",
    tags=common_tags,
)

# Policy for S3 access (MLflow artifacts, models)
s3_access_policy = aws.iam.RolePolicy(
    "app-runner-s3-policy",
    role=app_runner_role.id,
    policy=data_bucket.arn.apply(
        lambda arn: f"""{{
        "Version": "2012-10-17",
        "Statement": [{{
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket",
                "s3:DeleteObject"
            ],
            "Resource": [
                "{arn}",
                "{arn}/*"
            ]
        }}]
    }}"""
    ),
)

# IAM Role for EC2 Monitoring Instance
ec2_monitoring_role = aws.iam.Role(
    "ec2-monitoring-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    }""",
    tags=common_tags,
)

# Attach CloudWatch policy for monitoring
cloudwatch_policy_attachment = aws.iam.RolePolicyAttachment(
    "ec2-cloudwatch-policy",
    role=ec2_monitoring_role.name,
    policy_arn="arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
)

# Instance profile for EC2
ec2_instance_profile = aws.iam.InstanceProfile(
    "monitoring-instance-profile",
    role=ec2_monitoring_role.name,
)

# ============================================
# Security Groups
# ============================================

# Security group for monitoring EC2 instance
monitoring_sg = aws.ec2.SecurityGroup(
    "monitoring-security-group",
    description="Security group for Prometheus and Grafana monitoring stack",
    ingress=[
        # SSH
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],
            description="SSH access",
        ),
        # HTTP (Nginx)
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
            description="HTTP for Nginx reverse proxy",
        ),
        # Prometheus
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=9090,
            to_port=9090,
            cidr_blocks=["0.0.0.0/0"],
            description="Prometheus",
        ),
        # Grafana
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=3000,
            to_port=3000,
            cidr_blocks=["0.0.0.0/0"],
            description="Grafana",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound traffic",
        )
    ],
    tags=common_tags,
)

# ============================================
# EC2 Instance for Monitoring Stack
# ============================================

# User data script to install Docker, Prometheus, and Grafana
monitoring_user_data = """#!/bin/bash
set -e

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Nginx
amazon-linux-extras install -y nginx1
systemctl start nginx
systemctl enable nginx

# Create monitoring directory
mkdir -p /opt/monitoring/{prometheus,grafana}
chown -R ec2-user:ec2-user /opt/monitoring

# Create Prometheus config
cat > /opt/monitoring/prometheus/prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'card-approval-api'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']
EOF

# Create docker-compose.yml for monitoring stack
cat > /opt/monitoring/docker-compose.yml <<'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
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
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
EOF

# Configure Nginx reverse proxy
cat > /etc/nginx/conf.d/monitoring.conf <<'EOF'
server {
    listen 80;
    server_name _;

    location /grafana/ {
        proxy_pass http://localhost:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /prometheus/ {
        proxy_pass http://localhost:9090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Restart Nginx
systemctl restart nginx

# Start monitoring stack
cd /opt/monitoring
docker-compose up -d

echo "Monitoring stack installation complete!"
"""

# Get latest Amazon Linux 2 AMI
ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["amazon"],
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["amzn2-ami-hvm-*-x86_64-gp2"],
        ),
    ],
)

# EC2 instance for monitoring
monitoring_instance = aws.ec2.Instance(
    "monitoring-instance",
    instance_type="t3.medium",
    ami=ami.id,
    iam_instance_profile=ec2_instance_profile.name,
    vpc_security_group_ids=[monitoring_sg.id],
    user_data=monitoring_user_data,
    tags={**common_tags, "Name": f"{project_name}-monitoring"},
)

# ============================================
# Outputs
# ============================================

export("s3_bucket_name", data_bucket.id)
export("s3_bucket_arn", data_bucket.arn)
export("s3_bucket_url", data_bucket.bucket.apply(lambda b: f"s3://{b}"))
export("app_runner_role_arn", app_runner_role.arn)
export("monitoring_instance_id", monitoring_instance.id)
export("monitoring_instance_public_ip", monitoring_instance.public_ip)
export("monitoring_instance_public_dns", monitoring_instance.public_dns)
export(
    "grafana_url",
    monitoring_instance.public_ip.apply(lambda ip: f"http://{ip}/grafana/"),
)
export(
    "prometheus_url",
    monitoring_instance.public_ip.apply(lambda ip: f"http://{ip}/prometheus/"),
)
export("aws_region", aws_region)

# Instructions
export(
    "next_steps",
    pulumi.Output.concat(
        "Infrastructure deployed successfully!\n\n",
        "1. S3 Bucket: ", data_bucket.id, "\n",
        "2. Monitoring Dashboard: http://", monitoring_instance.public_ip, "/grafana/\n",
        "3. Prometheus: http://", monitoring_instance.public_ip, "/prometheus/\n",
        "4. Default Grafana credentials: admin/admin\n\n",
        "Next: Configure DVC with S3 bucket and deploy App Runner service",
    ),
)
