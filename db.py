import os
import psycopg2
import pandas as pd

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("Database not set")

TABLE = "weight_log"

def get_conn():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE}(
        id SERIAL PRIMARY KEY,
        weight REAL NOT NULL,
        date DATE NOT NULL UNIQUE
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def insert_or_update_log(date, weight):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO {TABLE} (date, weight) VALUES (%s,%s)
        ON CONFLICT(date) DO UPDATE SET weight = EXCLUDED.weight;
    """,
    (date, weight)
    )
    conn.commit()
    cur.close()
    conn.close()

def load_all_logs():
    conn = get_conn()
    df = pd.read_sql(f"SELECT id, weight, date FROM {TABLE} ORDER BY date ASC", conn)
    conn.close()
    return df

def delete_log(log_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {TABLE} where id = %s", (log_id,)
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_all():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {TABLE}")
    conn.commit()
    cur.close()
    conn.close()