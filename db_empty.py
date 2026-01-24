import sqlite3
from pathlib import Path
import pandas as pd

CSV_path = Path("weight_log.csv")
DB_path = Path("weight_log.db")
Table_name = "weight_log"

conn = sqlite3.connect(DB_path)
cur = conn.cursor()

cur.execute(f"DELETE FROM {Table_name}")
conn.commit()
cur.execute(f"SELECT COUNT(*) FROM {Table_name};")
count = cur.fetchone()[0]

print(f"✅ Migration done. Rows in {Table_name}: {count}")