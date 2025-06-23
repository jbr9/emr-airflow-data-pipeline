from airflow.operators.python import PythonOperator
from airflow import DAG
import subprocess
import datetime

def list_packages():
    result = subprocess.run(["pip", "list"], capture_output=True, text=True)
    print(result.stdout)  # Logs packages in Airflow UI

with DAG("check_mwaa_packages", start_date=datetime.datetime(2024, 1, 1), schedule_interval=None) as dag:
    check_packages = PythonOperator(
        task_id="list_packages",
        python_callable=list_packages
    )