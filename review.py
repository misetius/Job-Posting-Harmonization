import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    dbname=os.getenv("POSTGRES_DB", "postgres"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
)

sql_query = """
    SELECT raw_title, canonical_title, job_id FROM harmonized_jobs ORDER BY job_id LIMIT 100;
    """

cursor = conn.cursor()
cursor.execute(sql_query)

results = cursor.fetchall()

with open("harmonized_jobs.csv", "w") as f:
    f.write("Review : Raw Title : Canonical Title\n")
    for row in results:
        raw_title, canonical_title, job_id = row
        f.write(f" : {raw_title} : {canonical_title} : {job_id}\n")

cursor.close()
conn.close()

