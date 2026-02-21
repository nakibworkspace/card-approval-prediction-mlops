"""
Airflow DAG for Credit Card Approval ML Training Pipeline

This DAG orchestrates the end-to-end ML training workflow:
1. Download data from Kaggle
2. Preprocess and feature engineering
3. Train multiple models
4. Evaluate model quality
5. Register best model to MLflow Production
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator
from airflow.utils.trigger_rule import TriggerRule

# Default arguments for all tasks
default_args = {
    "owner": "mlops-team",
    "depends_on_past": False,
    "email": ["mlops@example.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    "credit_card_ml_pipeline",
    default_args=default_args,
    description="End-to-end ML training pipeline for credit card approval prediction",
    schedule_interval="0 2 * * 0",  # Every Sunday at 2 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ml", "training", "credit-card", "mlops"],
    max_active_runs=1,
)

# Task 1: Download data from Kaggle
download_data = BashOperator(
    task_id="download_data",
    bash_command="""
    cd /opt/airflow/training && \
    python scripts/download_data.py
    """,
    dag=dag,
)

# Task 2: Run EDA (optional, for monitoring)
run_eda = BashOperator(
    task_id="run_eda",
    bash_command="""
    cd /opt/airflow/training && \
    python scripts/run_eda.py
    """,
    dag=dag,
)

# Task 3: Preprocess data
preprocess_data = BashOperator(
    task_id="preprocess_data",
    bash_command="""
    cd /opt/airflow/training && \
    python scripts/run_preprocessing.py
    """,
    dag=dag,
)

# Task 4: Train models with MLflow tracking
train_models = BashOperator(
    task_id="train_models",
    bash_command="""
    cd /opt/airflow/training && \
    python scripts/run_training.py \
        --mlflow-uri ${MLFLOW_TRACKING_URI} \
        --auto-register \
        --model-name card_approval_model \
        --metric F1-Score
    """,
    env={
        "MLFLOW_TRACKING_URI": "{{ var.value.mlflow_tracking_uri }}",
        "AWS_ACCESS_KEY_ID": "{{ var.value.aws_access_key_id }}",
        "AWS_SECRET_ACCESS_KEY": "{{ var.value.aws_secret_access_key }}",
        "AWS_DEFAULT_REGION": "{{ var.value.aws_region }}",
    },
    dag=dag,
)

# Task 5: Evaluate model quality gate
evaluate_model = BashOperator(
    task_id="evaluate_model",
    bash_command="""
    python /opt/airflow/scripts/evaluate_model.py \
        --model-name card_approval_model \
        --stage Production \
        --min-f1 0.75 \
        --mlflow-uri ${MLFLOW_TRACKING_URI}
    """,
    env={
        "MLFLOW_TRACKING_URI": "{{ var.value.mlflow_tracking_uri }}",
        "AWS_ACCESS_KEY_ID": "{{ var.value.aws_access_key_id }}",
        "AWS_SECRET_ACCESS_KEY": "{{ var.value.aws_secret_access_key }}",
    },
    dag=dag,
)

# Task 6: Send notification
send_notification = PythonOperator(
    task_id="send_notification",
    python_callable=lambda: print("Pipeline completed successfully!"),
    trigger_rule=TriggerRule.ALL_DONE,
    dag=dag,
)

# Define task dependencies
download_data >> run_eda >> preprocess_data >> train_models >> evaluate_model >> send_notification
