from datetime import datetime
from flask import Flask, request
from google.cloud import bigquery

import getpass, os, platform, socket

app=Flask("CloudRunSimple")
client = bigquery.Client()
table_id = "gcp-project-375309.ml.user_table"

@app.route('/')
def main(bq_client = client):

    user = "unknown"
    try:
        user = getpass.getuser()
    except Exception:
        user = "unknown"

    cloud_run = "K_SERVICE" in os.environ

    if cloud_run:
        server = os.getenv("K_REVISION") or socket.gethostname()
    else:
        server = os.getenv("LOGONSERVER") or socket.gethostname()

    processor = os.getenv("PROCESSOR_ARCHITECTURE") or platform.machine()
    oper_sys = os.getenv("OS") or platform.system()
    record_date = datetime.now().date()
    create_ts = datetime.now()
    
    query = f"""
        INSERT INTO `{table_id}` (user, server, os, processor, record_date, create_timestamp)
        VALUES (@user, @server, @os, @processor, @record_date, @create_ts)
    """
    job_config = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter("user", "STRING", user),
        bigquery.ScalarQueryParameter("server", "STRING", server),
        bigquery.ScalarQueryParameter("os", "STRING", oper_sys),
        bigquery.ScalarQueryParameter("processor", "STRING", processor),
        bigquery.ScalarQueryParameter("record_date", "DATE", record_date),
        bigquery.ScalarQueryParameter("create_ts", "TIMESTAMP", create_ts),
    ])
    print(query)
    query_job = client.query(query, job_config=job_config)
    query_job.result()
    print("SQL insert complete.")

    dest_table = bq_client.get_table(table=table_id)
    return {"data" : dest_table.num_rows}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port = int(os.environ.get("PORT", 5052)))
    