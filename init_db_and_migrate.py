import sqlite3
from pathlib import Path
import pandas as pd

CSV_path = Path("weight_log.csv")
DB_path = Path("weight_log.db")
Table_name = "weight_log"

conn = sqlite3.connect(DB_path)
cur = conn.cursor()

cur.execute(
    f"""
    CREATE TABLE if not exists {Table_name}(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,
    weight REAL NOT NULL
    );
    """
)

conn.commit()

if not CSV_path.exists():
    raise FileNotFoundError(f"CSV not found at: {CSV_path}")

df = pd.read_csv(CSV_path)

df['date'] = pd.to_datetime(df['date'], format = "mixed", errors = "coerce")
df = df.dropna(subset = ['date'])

df['date'] = df['date'].dt.date.astype(str)

df['weight'] = pd.to_numeric(df['weight'], errors = "coerce")
df = df.dropna(subset = ['weight'])

df = df[['date', 'weight']] # WE CAN ONLY HAVE & WANT 2 COLUMNS.

rows_toinsert = list(df.itertuples(name = None, index = False)) # WE GIVE TUPLE VALUE TO INSERT REPLACE DATA IN A DB

cur.executemany(
    f"""
    INSERT OR REPLACE INTO {Table_name}(date, weight)
    VALUES(?,?);
    """, 
    rows_toinsert
)

conn.commit()

cur.execute(f"SELECT COUNT(*) FROM {Table_name};")
count = cur.fetchone()[0]

print(f"✅ Migration done. Rows in {Table_name}: {count}")

conn.close() # ALWAYS CLOSE WHEN FINISHED TO AVOID LOCKING ISSUES