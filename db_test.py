import pandas as pd
import sqlite3

conn = sqlite3.connect("weight_log.db")

df = pd.read_sql("SELECT * FROM weight_log", conn)
print(df)

conn.close()