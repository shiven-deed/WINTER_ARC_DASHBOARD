# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import time
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3

st.set_page_config(page_title="WINTER ARC DASHBOARD", layout="centered")
st.title("❄️ WINTER ARC")

FILE_PATH = "weight_log.csv"
DB_PATH = "weight_log.db"
TABLE = "weight_log"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread = False)

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

init_db()

# ==========================================
# 2. SIDEBAR (INPUTS)
# ==========================================
st.sidebar.header("📝 LOG DATA")
with st.sidebar.form("entry_form"):
    weight_input = st.number_input("Weight (kg):", step=0.1, format="%.1f")
    date_input = st.date_input("Date:", value=dt.date.today())
    submit_log = st.form_submit_button("LOG ENTRY")

st.sidebar.divider()

st.sidebar.header("🎯 GOAL SETTINGS")
enable_goals = st.sidebar.checkbox("Enable Goal Tracking")

if enable_goals:
    goal_weight = st.sidebar.number_input("Target Weight (kg):", value=75, step=1)
    goal_date = st.sidebar.date_input("Target Date:", value=dt.date(2026, 1, 31))
    # Convert to timestamp immediately for math
    goal_date = pd.to_datetime(goal_date)

# ==========================================
# 3. DATA PROCESSING (The "Brain")
# ==========================================
# A. Handle New Log Entry
if submit_log:
    try:
        conn = get_conn()

        conn.execute(f"""
            INSERT OR REPLACE into {TABLE}(date, weight)
            VALUES(?,?)
        """, (date_input, weight_input))
        conn.commit()
        conn.close()

        st.sidebar.success("✅ Saved to SQL")
        time.sleep(0.5)

    except Exception as e:
        st.sidebar.error(f"Error: {e}")

    st.rerun()
# B. Load & Prep Data
try:
    conn = get_conn()
    df = pd.read_sql(f"SELECT * FROM {TABLE} ORDER BY date ASC", conn)# Critical for graphing
    conn.close()

    if df.empty:
        st.warning("⚠️ Database is empty. Log your first weight!")
        st.stop()

    df['date'] = pd.to_datetime(df['date'], format = 'mixed')
    df['rolling_avg'] = df['weight'].rolling(window = 7, min_periods = 2).mean()

except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop() # Stop execution here if no data

# C. Machine Learning (Linear Regression)
df['date_ordinal'] = df['date'].map(dt.datetime.toordinal)
X = df[['date_ordinal']]
y = df['weight']

model = LinearRegression()
model.fit(X, y)

# D. Calculations (The "Truth")
current_weight = df['weight'].iloc[-1]
actual_slope = model.coef_[0]

# Required Slope Math (Only if Goals are Enabled)
status = "⚪ NO GOAL SET" # Default
if enable_goals:
    today = pd.Timestamp.now().normalize()
    days_left = (goal_date - today).days
    
    if days_left <= 0:
        required_slope = 0
    else:
        required_slope = (goal_weight - current_weight) / days_left
        
    status = "✅ ON TRACK" if actual_slope <= required_slope else "⚠️ OFF TRACK"

# ==========================================
# 4. VISUALIZATION (The "Face")
# ==========================================
st.divider()

# A. Key Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Current Weight", f"{current_weight:.1f} kg")

# Calculate 14-day prediction
future_ordinal_14 = (pd.Timestamp.now() + dt.timedelta(days=14)).toordinal()
pred_14 = model.predict([[future_ordinal_14]])[0]
col2.metric("Predicted (14 Days)", f"{pred_14:.1f} kg")

if status == "✅ ON TRACK":
    col3.success(status)
elif status == "⚠️ OFF TRACK":
    col3.error(status)
else:
    col3.info(status)

# B. The Visual Oracle (Chart)
st.subheader("The Visual Oracle")

fig, ax = plt.subplots(figsize=(10, 5))

# 1. Actual Data (Blue Dots)
ax.scatter(df['date'], df['weight'], color='blue', alpha=0.6, label='Actual')

# 2. Trend Line (Red Dashed) - Projected 14 Days
future_days = 14
last_date = df['date'].max()
future_dates = pd.date_range(start=df['date'].min(), end=last_date + pd.Timedelta(days=future_days))
future_ordinals = future_dates.map(dt.datetime.toordinal).values.reshape(-1, 1)
future_preds = model.predict(future_ordinals)

ax.plot(future_dates, future_preds, color='red', linestyle='--', label='Trend')

# 3. Ideal Path (Green Dashed) - Only if Goal Enabled
if enable_goals:
    start_date = df['date'].iloc[0]
    start_weight = df['weight'].iloc[0]
    ax.plot([start_date, goal_date], [start_weight, goal_weight], color='green', linestyle=':', linewidth=2, label='Ideal')
# 4. ROLLING AVG(ORANGE DASHED)
ax.plot(df['date'], df['rolling_avg'], color = 'orange', linewidth = 2, linestyle = '--', label = '7 days average')

# Formatting
ax.set_title(f"Trajectory vs Goal")
ax.grid(True, linestyle=':', alpha=0.4)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.legend()
plt.xticks(rotation=45)

st.pyplot(fig)

# C. Raw Data Table (Expander to keep UI clean)
st.divider()
st.subheader("🛠️ Manage Data")

with st.expander("VIEW & EDIT HISTORY"):
    # A. DATE RANGE FILTER
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    
    col1, col2 = st.columns(2) # MAKING COLUMNS FOR INPUT
    start_date = col1.date_input("Start date", min_date)
    end_date = col2.date_input("End date", max_date)
    mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date) # MASKING FOR FILTER
    filtered_date = df.loc[mask][['date', 'weight']]

    st.write(f"Showing {len(filtered_date)} entries: ") # DISPLAY
    st.dataframe(filtered_date.style.format({'date': lambda x: x.strftime("%Y-%m-%d"), 'weight': '{:.1f}'}))

    # B. DELETE INTERFACE
    delete = (df.apply(lambda x: f"{x['date'].strftime("%Y-%m-%d")} | {x['weight']}", axis = 1)).to_list()[::-1]
    selected_option = st.selectbox(
            "Select entry to delete: ",
            options = delete,
            index= None,
            placeholder = "Select an entry ..."
    )
    if selected_option:
        if st.button(f"🗑️ PERMANENTLY DELETE {selected_option.split(" | ")[0]}"):
            delete_key = selected_option.split(" | ")[0]

            try:
                conn = get_conn()

                conn.execute(f"DELETE FROM {TABLE} WHERE date = ?", (delete_key,))
                # IMPORTANT: SQL EXPECTS TUPLE MAKE A STRING TUPLE BY ADDING ",".
                conn.commit()
                conn.close()

                st.success(f"✅ Deleted entry for {delete_key}")
                time.sleep(1)
            except Exception as e:
                st.error(f"Could not delete {selected_option}: {e}")

            st.rerun() # Refresh to update graph and remove from list
with st.expander("📄 View Raw Data"):
    clean_df = df[['date', 'weight']].copy()
    st.dataframe(clean_df.style.format({"date": lambda t: t.strftime("%Y-%m-%d"), "weight": "{:.1f}"}))


# DOWNLOAD BUTTON
download = clean_df.to_csv(index = False).encode('utf-8')

st.download_button(
    label = '💾 DOWNLOAD BACKUP CSV',
    data = download,
    file_name = 'weight_winter.csv',
    mime = 'text/csv'
)