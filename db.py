import sqlite3
import pandas as pd

DB_PATH = "weight_log.db"
TABLE = "weight_log"

def get_conn():
    return sqlite3.connect(
        DB_PATH,
        check_same_thread = False,
        timeout = 10
        )

def init_db():
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE}(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        weight REAL NOT NULL,
        date TEXT NOT NULL UNIQUE
        );
    """)
    conn.commit()
    conn.close()

def insert_or_update_log(date, weight):
    conn = get_conn()
    conn.execute(f"""
        INSERT OR REPLACE INTO {TABLE} (date, weight) VALUES (?,?)
    """,
    (date, weight)
    )
    conn.commit()
    conn.close()

def load_all_logs():
    conn = get_conn()
    df = pd.read_sql(f"SELECT * FROM {TABLE} ORDER BY date ASC", conn)
    conn.close()
    return df

def delete_log(date):
    conn = get_conn()
    conn.execute(f"DELETE FROM {TABLE} where date = ?", (date,)
    )
    conn.commit()
    conn.close()

def delete_all():
    conn = get_conn()
    conn.execute(f"DELETE FROM {TABLE}")
    conn.commit()
    conn.close()