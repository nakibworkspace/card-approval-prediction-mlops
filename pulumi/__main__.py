"""
Pulumi Infrastructure as Code for Card Approval Prediction on AWS

3-instance architecture:
- EC2-1 (API):        t2.small  10.0.1.10 — FastAPI, PostgreSQL, Redis, Nginx
- EC2-2 (Airflow):    t2.medium 10.0.1.20 — MLflow, Airflow, PostgreSQL x2
- EC2-3 (Monitoring): t2.medium 10.0.1.30 — Prometheus, Grafana, Loki, Promtail, Tempo
- S3 for MLflow artifacts

Security: Single security group allowing all inbound/outbound traffic.
S3 access via AWS credentials passed through .env (CD pipeline).
"""

import pulumi
import pulumi_aws as aws
from pulumi import Config, export

# ============================================
# Configuration
# ============================================
config = Config()
project_name = "card-approval"
environment = config.get("environment") or "production"
aws_region = aws.get_region().name
ssh_key_name = config.require("ssh_key_name")
github_repo = config.get("github_repo") or "https://github.com/nakibworkspace/card-approval-prediction-mlops.git"
github_branch = config.get("github_branch") or "main"
dockerhub_username = config.get("dockerhub_username") or "nakibahmed"

common_tags = {
    "Project": project_name,
    "Environment": environment,
    "ManagedBy": "Pulumi",
}

# ============================================
# S3 Bucket — MLflow Artifacts
# ============================================
mlflow_bucket = aws.s3.Bucket(
    "mlflow-artifacts-bucket",
    bucket=f"{project_name}-mlflow-artifacts-{environment}",
    acl="private",
    versioning=aws.s3.BucketVersioningArgs(enabled=True),
    tags={**common_tags, "Purpose": "MLflow-Artifacts"},
)

aws.s3.BucketPublicAccessBlock(
    "mlflow-bucket-public-access-block",
    bucket=mlflow_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# ============================================
# VPC and Networking
# ============================================
vpc = aws.ec2.Vpc(
    "vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={**common_tags, "Name": f"{project_name}-vpc"},
)

igw = aws.ec2.InternetGateway(
    "igw",
    vpc_id=vpc.id,
    tags={**common_tags, "Name": f"{project_name}-igw"},
)

public_subnet = aws.ec2.Subnet(
    "public-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    availability_zone=f"{aws_region}a",
    tags={**common_tags, "Name": f"{project_name}-public-subnet"},
)

public_rt = aws.ec2.RouteTable(
    "public-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        ),
    ],
    tags={**common_tags, "Name": f"{project_name}-public-rt"},
)

aws.ec2.RouteTableAssociation(
    "public-rt-assoc",
    subnet_id=public_subnet.id,
    route_table_id=public_rt.id,
)

# ============================================
# Security Group — Allow ALL Traffic
# ============================================
allow_all_sg = aws.ec2.SecurityGroup(
    "allow-all-sg",
    vpc_id=vpc.id,
    description="Allow all inbound and outbound traffic",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="All inbound traffic",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="All outbound traffic",
        ),
    ],
    tags={**common_tags, "Name": f"{project_name}-allow-all-sg"},
)

# ============================================
# AMI — Ubuntu 22.04
# ============================================
ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],  # Canonical
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"],
        ),
    ],
)

# ============================================
# User Data — Bootstrap Script
# ============================================
# Installs Docker + Docker Compose and clones repo.
# Does NOT start services — the CD pipeline handles deployment.
user_data_bootstrap = f"""#!/bin/bash
set -euo pipefail
exec > /var/log/user-data.log 2>&1

echo "=== Starting bootstrap ==="

# Install Docker
apt-get update -y
apt-get install -y docker.io git curl
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu

# Install Docker Compose v2
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
ln -sf /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

# Clone repository
git clone -b {github_branch} {github_repo} /opt/app
chown -R ubuntu:ubuntu /opt/app

echo "=== Bootstrap complete ==="
"""

# ============================================
# EC2 Instances
# ============================================

# --- EC2-1: API Instance (FastAPI + PostgreSQL + Redis + Nginx) ---
api_instance = aws.ec2.Instance(
    "api-instance",
    instance_type="t2.small",
    ami=ami.id,
    subnet_id=public_subnet.id,
    private_ip="10.0.1.10",
    vpc_security_group_ids=[allow_all_sg.id],

    key_name=ssh_key_name,
    user_data=user_data_bootstrap,
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=20,
        volume_type="gp3",
    ),
    tags={**common_tags, "Name": f"{project_name}-api", "Role": "api"},
)

# --- EC2-2: Airflow + MLflow Instance ---
airflow_instance = aws.ec2.Instance(
    "airflow-instance",
    instance_type="t2.medium",
    ami=ami.id,
    subnet_id=public_subnet.id,
    private_ip="10.0.1.20",
    vpc_security_group_ids=[allow_all_sg.id],

    key_name=ssh_key_name,
    user_data=user_data_bootstrap,
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=30,
        volume_type="gp3",
    ),
    tags={**common_tags, "Name": f"{project_name}-airflow", "Role": "airflow-mlflow"},
)

# --- EC2-3: Monitoring Instance (Prometheus + Grafana + Loki + Promtail + Tempo) ---
monitoring_instance = aws.ec2.Instance(
    "monitoring-instance",
    instance_type="t2.medium",
    ami=ami.id,
    subnet_id=public_subnet.id,
    private_ip="10.0.1.30",
    vpc_security_group_ids=[allow_all_sg.id],

    key_name=ssh_key_name,
    user_data=user_data_bootstrap,
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=30,
        volume_type="gp3",
    ),
    tags={**common_tags, "Name": f"{project_name}-monitoring", "Role": "monitoring"},
)

# ============================================
# Outputs
# ============================================

# Networking
export("vpc_id", vpc.id)
export("subnet_id", public_subnet.id)
export("security_group_id", allow_all_sg.id)

# S3
export("s3_bucket_name", mlflow_bucket.bucket)
export("s3_bucket_arn", mlflow_bucket.arn)

# Instance IDs
export("api_instance_id", api_instance.id)
export("airflow_instance_id", airflow_instance.id)
export("monitoring_instance_id", monitoring_instance.id)

# Public IPs (use these for GitHub Secrets: EC2_API_HOST, EC2_AIRFLOW_HOST, EC2_MONITORING_HOST)
export("api_public_ip", api_instance.public_ip)
export("airflow_public_ip", airflow_instance.public_ip)
export("monitoring_public_ip", monitoring_instance.public_ip)

# Private IPs (used for inter-service communication)
export("api_private_ip", api_instance.private_ip)
export("airflow_private_ip", airflow_instance.private_ip)
export("monitoring_private_ip", monitoring_instance.private_ip)

# Service URLs
export("api_url", api_instance.public_ip.apply(lambda ip: f"http://{ip}"))
export("airflow_url", airflow_instance.public_ip.apply(lambda ip: f"http://{ip}:8080"))
export("mlflow_url", airflow_instance.public_ip.apply(lambda ip: f"http://{ip}:5000"))
export("grafana_url", monitoring_instance.public_ip.apply(lambda ip: f"http://{ip}:3000"))
export("prometheus_url", monitoring_instance.public_ip.apply(lambda ip: f"http://{ip}:9090"))
