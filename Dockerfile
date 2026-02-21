FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI for S3 access
RUN pip install --no-cache-dir awscli

RUN pip install --upgrade pip && \
    pip install --no-cache-dir uv

# Copy requirements first for better caching
COPY ./pyproject.toml .
RUN uv pip install . --system --no-cache-dir
RUN mkdir -p /app/reports

# Copy the rest of the application
COPY . .

# Create model and logs directories
# Models will be downloaded from MLflow at runtime if not present
RUN mkdir -p /app/models /app/logs

# Set environment variables
ENV AWS_DEFAULT_REGION=ap-southeast-1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "app.main"]
