import psycopg2

conn = psycopg2.connect(
    host='postgres-mlflow',
    port=5432,
    dbname='mlflow',
    user='mlflow_user',
    password='poridhian123'
)
cur = conn.cursor()
cur.execute("SELECT experiment_id FROM experiments WHERE name = 'credit_card_approval_model_training'")
rows = cur.fetchall()
for row in rows:
    exp_id = row[0]
    print(f'Deleting experiment {exp_id}...')
    # Get all run UUIDs for this experiment
    cur.execute("SELECT run_uuid FROM runs WHERE experiment_id = %s", (exp_id,))
    run_ids = [r[0] for r in cur.fetchall()]
    for run_id in run_ids:
        cur.execute("DELETE FROM tags WHERE run_uuid = %s", (run_id,))
        cur.execute("DELETE FROM metrics WHERE run_uuid = %s", (run_id,))
        cur.execute("DELETE FROM params WHERE run_uuid = %s", (run_id,))
        cur.execute("DELETE FROM latest_metrics WHERE run_uuid = %s", (run_id,))
        cur.execute("DELETE FROM model_versions WHERE run_id = %s", (run_id,))
    cur.execute("DELETE FROM runs WHERE experiment_id = %s", (exp_id,))
    cur.execute("DELETE FROM experiment_tags WHERE experiment_id = %s", (exp_id,))
    cur.execute("DELETE FROM experiments WHERE experiment_id = %s", (exp_id,))
    print(f'Permanently deleted experiment {exp_id} and {len(run_ids)} runs')
conn.commit()
cur.close()
conn.close()
print('Done')
