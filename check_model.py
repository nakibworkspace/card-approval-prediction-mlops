import mlflow
mlflow.set_tracking_uri('http://mlflow:5000')
client = mlflow.tracking.MlflowClient()
versions = client.search_model_versions("name='card_approval_model'")
if versions:
    for v in versions:
        print(f"Version: {v.version}, Stage: {v.current_stage}, Run ID: {v.run_id}")
else:
    print("No model versions found for card_approval_model")
