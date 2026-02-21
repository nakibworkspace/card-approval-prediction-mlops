import mlflow
mlflow.set_tracking_uri('http://mlflow:5000')
client = mlflow.tracking.MlflowClient()

# Find current Production model
versions = client.search_model_versions("name='card_approval_model'")
for v in versions:
    print(f"Version: {v.version}, Stage: {v.current_stage}, Run ID: {v.run_id}")
    artifacts = client.list_artifacts(v.run_id)
    print(f"  Artifacts: {[a.path for a in artifacts]}")
    for a in artifacts:
        if a.is_dir:
            sub = client.list_artifacts(v.run_id, a.path)
            print(f"    {a.path}/: {[s.path for s in sub]}")
    print()
