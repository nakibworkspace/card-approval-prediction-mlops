FROM apache/airflow:2.10.4-python3.11

USER root

# Install system dependencies if needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/airflow/training/data /opt/airflow/training/models /opt/airflow/training/outputs \
    && chown -R airflow:root /opt/airflow/training

USER airflow

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    kaggle \
    pandas \
    numpy \
    scikit-learn==1.3.2 \
    imbalanced-learn \
    xgboost==3.1.2 \
    lightgbm==4.1.0 \
    catboost==1.2.2 \
    mlflow==2.19.0 \
    boto3 \
    botocore \
    pyyaml \
    matplotlib \
    seaborn \
    evidently \
    joblib \
    scipy==1.15.3 \
    loguru
