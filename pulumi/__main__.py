"""
Pulumi Infrastructure as Code for Card Approval Prediction on AWS

3-instance architecture:
- EC2-1 (API):        t2.small  10.0.1.10 — FastAPI, PostgreSQL, Redis, Nginx
- EC2-2 (Airflow):    t2.medium 10.0.1.20 — MLflow, Airflow, PostgreSQL x2
- EC2-3 (Monitoring): t2.medium 10.0.1.30 — Prometheus, Grafana, Loki, Promtail, Tempo
- S3 for MLflow artifacts
"""

import pulumi
import pulumi_aws as aws
from pulumi import Config, export

# Configuration
config = Config()
project_name = "card-approval-prediction"
environment = config.get("environment") or "production"
aws_region = aws.get_region().name
ssh_key_name = config.require("ssh_key_name")

# Tags for all resources
common_tags = {
    "Project": project_name,
    "Environment": environment,
    "ManagedBy": "Pulumi",
}

# ============================================
# S3 Buckets
# ============================================

# Main data bucket for MLflow artifacts
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
    tags={**common_tags, "Purpose": "MLflow-Artifacts"},
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
# VPC and Networking
# ============================================

# VPC
vpc = aws.ec2.Vpc(
    "monitoring-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={**common_tags, "Name": f"{project_name}-vpc"},
)

# Internet Gateway
igw = aws.ec2.InternetGateway(
    "monitoring-igw",
    vpc_id=vpc.id,
    tags={**common_tags, "Name": f"{project_name}-igw"},
)

# Public Subnet
public_subnet = aws.ec2.Subnet(
    "monitoring-public-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    availability_zone=f"{aws_region}a",
    tags={**common_tags, "Name": f"{project_name}-public-subnet"},
)

# Route Table
public_route_table = aws.ec2.RouteTable(
    "monitoring-public-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        ),
    ],
    tags={**common_tags, "Name": f"{project_name}-public-rt"},
)

# Route Table Association
public_rt_association = aws.ec2.RouteTableAssociation(
    "monitoring-public-rt-assoc",
    subnet_id=public_subnet.id,
    route_table_id=public_route_table.id,
)

# ============================================
# Additional Configuration
# ============================================
github_repo = config.get("github_repo") or "https://github.com/nakib-ahmed/card-approval-prediction-mlops.git"
github_branch = config.get("github_branch") or "main"

vpc_cidr = "10.0.0.0/16"

# ============================================
# Security Groups
# ============================================

# --- API Security Group (EC2-1) ---
api_sg = aws.ec2.SecurityGroup(
    "api-security-group",
    vpc_id=vpc.id,
    description="Security group for API instance (FastAPI, Nginx)",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=22, to_port=22,
            cidr_blocks=["0.0.0.0/0"], description="SSH",
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=80, to_port=80,
            cidr_blocks=["0.0.0.0/0"], description="HTTP (Nginx)",
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=8000, to_port=8000,
            cidr_blocks=[vpc_cidr], description="FastAPI from VPC (Prometheus scrape)",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1", from_port=0, to_port=0,
            cidr_blocks=["0.0.0.0/0"], description="All outbound",
        ),
    ],
    tags={**common_tags, "Name": f"{project_name}-api-sg"},
)

# --- Airflow/MLflow Security Group (EC2-2) ---
airflow_sg = aws.ec2.SecurityGroup(
    "airflow-security-group",
    vpc_id=vpc.id,
    description="Security group for Airflow/MLflow instance",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=22, to_port=22,
            cidr_blocks=["0.0.0.0/0"], description="SSH",
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=5000, to_port=5000,
            cidr_blocks=[vpc_cidr], description="MLflow from VPC",
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=8080, to_port=8080,
            cidr_blocks=["0.0.0.0/0"], description="Airflow Webserver",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1", from_port=0, to_port=0,
            cidr_blocks=["0.0.0.0/0"], description="All outbound",
        ),
    ],
    tags={**common_tags, "Name": f"{project_name}-airflow-sg"},
)

# --- Monitoring Security Group (EC2-3) ---
monitoring_sg = aws.ec2.SecurityGroup(
    "monitoring-security-group",
    vpc_id=vpc.id,
    description="Security group for Monitoring instance (Prometheus, Grafana, Loki, Tempo)",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=22, to_port=22,
            cidr_blocks=["0.0.0.0/0"], description="SSH",
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=3000, to_port=3000,
            cidr_blocks=["0.0.0.0/0"], description="Grafana",
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=9090, to_port=9090,
            cidr_blocks=["0.0.0.0/0"], description="Prometheus",
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=3100, to_port=3100,
            cidr_blocks=[vpc_cidr], description="Loki from VPC",
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp", from_port=4317, to_port=4318,
            cidr_blocks=[vpc_cidr], description="Tempo OTLP (gRPC+HTTP) from VPC",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1", from_port=0, to_port=0,
            cidr_blocks=["0.0.0.0/0"], description="All outbound",
        ),
    ],
    tags={**common_tags, "Name": f"{project_name}-monitoring-sg"},
)

# ============================================
# User Data Scripts
# ============================================

# Common preamble: install Docker, Docker Compose, git, clone repo
_user_data_preamble = f"""#!/bin/bash
set -ex
exec > /var/log/user-data.log 2>&1

# Install Docker
apt-get update -y
apt-get install -y docker.io git
systemctl start docker
systemctl enable docker
usermod -a -G docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Clone repository
git clone -b {github_branch} {github_repo} /opt/app
cd /opt/app
"""

# --- API instance user data ---
api_user_data = pulumi.Output.all(
    data_bucket.bucket,
).apply(lambda args: _user_data_preamble + f"""
# Write .env
cat > /opt/app/.env <<'ENVEOF'
POSTGRES_API_PASSWORD=${{POSTGRES_API_PASSWORD:-api_password}}
REDIS_PASSWORD=${{REDIS_PASSWORD:-redis_password}}
MLFLOW_TRACKING_URI=http://10.0.1.20:5000
OTEL_EXPORTER_ENDPOINT=http://10.0.1.30:4317
OTEL_ENABLED=true
AWS_ACCESS_KEY_ID=${{AWS_ACCESS_KEY_ID}}
AWS_SECRET_ACCESS_KEY=${{AWS_SECRET_ACCESS_KEY}}
AWS_REGION=${{AWS_REGION:-us-east-1}}
S3_BUCKET_NAME={args[0]}
ENVEOF

# Start API stack
cd /opt/app
docker-compose -f docker-compose.api.yml up -d

echo "API instance setup complete!"
""")

# --- Airflow/MLflow instance user data ---
airflow_user_data = pulumi.Output.all(
    data_bucket.bucket,
).apply(lambda args: _user_data_preamble + f"""
# Write .env
cat > /opt/app/.env <<'ENVEOF'
POSTGRES_MLFLOW_PASSWORD=${{POSTGRES_MLFLOW_PASSWORD:-mlflow_password}}
POSTGRES_AIRFLOW_PASSWORD=${{POSTGRES_AIRFLOW_PASSWORD:-airflow_password}}
AIRFLOW_FERNET_KEY=${{AIRFLOW_FERNET_KEY:-fb0c3f8c8b3f4c5e8d9a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e}}
AIRFLOW_SECRET_KEY=${{AIRFLOW_SECRET_KEY:-secret}}
AIRFLOW_ADMIN_PASSWORD=${{AIRFLOW_ADMIN_PASSWORD:-admin}}
AWS_ACCESS_KEY_ID=${{AWS_ACCESS_KEY_ID}}
AWS_SECRET_ACCESS_KEY=${{AWS_SECRET_ACCESS_KEY}}
AWS_REGION=${{AWS_REGION:-us-east-1}}
S3_BUCKET_NAME={args[0]}
KAGGLE_USERNAME=${{KAGGLE_USERNAME}}
KAGGLE_KEY=${{KAGGLE_KEY}}
ENVEOF

# Start Airflow/MLflow stack
cd /opt/app
docker-compose -f docker-compose.airflow.yml up -d

echo "Airflow/MLflow instance setup complete!"
""")

# --- Monitoring instance user data ---
monitoring_user_data = _user_data_preamble + """
# Write .env
cat > /opt/app/.env <<'ENVEOF'
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
ENVEOF

# Start Monitoring stack
cd /opt/app
docker-compose -f docker-compose.monitoring.yml up -d

echo "Monitoring instance setup complete!"
"""

# ============================================
# AMI
# ============================================

ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],  # Canonical (Ubuntu)
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"],
        ),
    ],
)

# ============================================
# EC2 Instances
# ============================================

# --- EC2-1: API Instance ---
api_instance = aws.ec2.Instance(
    "api-instance",
    instance_type="t2.small",
    ami=ami.id,
    subnet_id=public_subnet.id,
    private_ip="10.0.1.10",
    vpc_security_group_ids=[api_sg.id],
    key_name=ssh_key_name,
    user_data=api_user_data,
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=20,
        volume_type="gp3",
    ),
    tags={**common_tags, "Name": f"{project_name}-api"},
)

# --- EC2-2: Airflow/MLflow Instance ---
airflow_instance = aws.ec2.Instance(
    "airflow-instance",
    instance_type="t2.medium",
    ami=ami.id,
    subnet_id=public_subnet.id,
    private_ip="10.0.1.20",
    vpc_security_group_ids=[airflow_sg.id],
    key_name=ssh_key_name,
    user_data=airflow_user_data,
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=30,
        volume_type="gp3",
    ),
    tags={**common_tags, "Name": f"{project_name}-airflow"},
)

# --- EC2-3: Monitoring Instance ---
monitoring_instance = aws.ec2.Instance(
    "monitoring-instance",
    instance_type="t2.medium",
    ami=ami.id,
    subnet_id=public_subnet.id,
    private_ip="10.0.1.30",
    vpc_security_group_ids=[monitoring_sg.id],
    key_name=ssh_key_name,
    user_data=monitoring_user_data,
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=30,
        volume_type="gp3",
    ),
    tags={**common_tags, "Name": f"{project_name}-monitoring"},
)

# ============================================
# Outputs
# ============================================

export("vpc_id", vpc.id)
export("public_subnet_id", public_subnet.id)
export("s3_bucket_name", data_bucket.id)
export("s3_bucket_arn", data_bucket.arn)
export("s3_bucket_url", data_bucket.bucket.apply(lambda b: f"s3://{b}"))
export("aws_region", aws_region)

# Instance IDs
export("api_instance_id", api_instance.id)
export("airflow_instance_id", airflow_instance.id)
export("monitoring_instance_id", monitoring_instance.id)

# Public IPs
export("api_public_ip", api_instance.public_ip)
export("airflow_public_ip", airflow_instance.public_ip)
export("monitoring_public_ip", monitoring_instance.public_ip)

# Private IPs
export("api_private_ip", api_instance.private_ip)
export("airflow_private_ip", airflow_instance.private_ip)
export("monitoring_private_ip", monitoring_instance.private_ip)

# Convenience URLs
export("api_url", api_instance.public_ip.apply(lambda ip: f"http://{ip}"))
export("mlflow_url", airflow_instance.public_ip.apply(lambda ip: f"http://{ip}:5000"))
export("airflow_url", airflow_instance.public_ip.apply(lambda ip: f"http://{ip}:8080"))
export("grafana_url", monitoring_instance.public_ip.apply(lambda ip: f"http://{ip}:3000"))
export("prometheus_url", monitoring_instance.public_ip.apply(lambda ip: f"http://{ip}:9090"))
