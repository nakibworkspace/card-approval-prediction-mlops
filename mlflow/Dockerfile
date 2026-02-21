FROM ghcr.io/mlflow/mlflow:v2.9.2

# Install PostgreSQL adapter
RUN pip install --no-cache-dir psycopg2-binary

# Install AWS SDK for S3 support
RUN pip install --no-cache-dir boto3

EXPOSE 5000

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]
