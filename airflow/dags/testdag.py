from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 2, 19),  # Changed to a past date
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    "run_spark_job_bash",
    default_args=default_args,
    description="Run a PySpark job using bash command in Airflow",
    schedule_interval="*/5 * * * *",  # Runs daily
    catchup=False,  # Avoid running past missed schedules
    max_active_runs=1,  # Ensures only one instance runs at a time
    concurrency=1
)

# Define BashOperator to run Spark job
spark_task = BashOperator(
    task_id="run_spark_job",
    bash_command='spark-submit --jars /mnt/c/spark/spark-3.5.2-bin-hadoop3/jars/postgresql-42.7.5.jar /home/nitesh/project_1/youtube_project/spark_jobs/testjob.py',
    dag=dag,
)

# Task sequence
spark_task
