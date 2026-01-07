# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import time
import sqlite3
import os  # Needed to check for old CSV file
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


st.set_page_config(page_title="WINTER ARC DASHBOARD", layout="centered")
st.title("❄️ WINTER ARC")

# --- DATABASE CONFIGURATION ---
DB_FILE = 'weight_log.db'
OLD_CSV_FILE = "weight_log.csv"

# --- DATABASE FUNCTIONS (The Engine Room) ---
def get_connection():
    """Creates a database connection."""
    # check_same_thread=False is needed for Streamlit's concurrency model
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    """Creates the table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weigh_ins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            weight REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()



def load_data_from_db():
    """Reads all weigh-ins and returns a DataFrame."""
    conn = get_connection()
    try:
        # SQL -> Pandas
        df = pd.read_sql("SELECT date, weight FROM weigh_ins ORDER BY date ASC", conn)
    finally:
        conn.close()
    
    if df.empty:
        return pd.DataFrame(columns=['date', 'weight'])
    return df

def insert_weigh_in(date_str, weight_val):
    """Inserts or updates a record."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO weigh_ins (date, weight) VALUES (?, ?)",
            (date_str, weight_val)
        )
        conn.commit()
    except Exception as e:
        raise e
    finally:
        conn.close()

# --- INITIALIZE ON STARTUP ---
init_db()
def get_ai_response(user_prompt):
    try:
        client = Groq(api_key = st.secrets['GROQ_API_KEY'])

        completion = client.chat.completions.create(
            model = "llama-3.1-8b-instant",
            messages = [{
                "role" : "system",
                "content" : "You are a Winter Arc Coach. You are tough, stoic, and focused on discipline. Your goal is to keep the user on track with their weight goals. Be brief (2-3 sentences max). Roast them slightly if they are making excuses."
                }, {
                    "role" : "user",
                    "content" : user_prompt
                }],
            temperature = 1,
            top_p = 1,
            max_tokens = 200,
            stream = False,
            stop = None
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error occured connecting to coach: {e}"
# ==========================================
# 2. SIDEBAR (INPUTS)
# ==========================================
st.sidebar.header("📝 LOG DATA")
with st.sidebar.form("entry_form"):
    weight_input = st.number_input("Weight (kg):", step=0.1, format="%.1f")
    # Default to today
    date_input = st.date_input("Date:", value=dt.date.today())
    submit_log = st.form_submit_button("LOG ENTRY")

st.sidebar.divider()

st.sidebar.header("🎯 GOAL SETTINGS")
enable_goals = st.sidebar.checkbox("Enable Goal Tracking")

if enable_goals:
    goal_weight = st.sidebar.number_input("Target Weight (kg):", value=75, step=1)
    goal_date = st.sidebar.date_input("Target Date:", value=dt.date(2026, 1, 31))
    goal_date = pd.to_datetime(goal_date)

# AI HELP
st.sidebar.divider()
st.sidebar.header("🤖 WINTER ARC COACH")

button = st.sidebar.button("GET HELP...")
with st.spinner("Opening chat"):
    user_query = st.sidebar.text_area("Enter the prompt: ")

if button:
    if user_query:
        with st.sidebar.status("Connecting to Groq..."):
            time.sleep(2)
            st.sidebar.info(get_ai_response(user_query))
    else:
        st.sidebar.warning("You must say something first.")


# ==========================================
# 3. DATA PROCESSING (The "Brain")
# ==========================================

# A. Handle New Log Entry
if submit_log:
    try:
        # 1. Convert date to string for SQLite (YYYY-MM-DD)
        date_str = date_input.strftime("%Y-%m-%d")
        
        # 2. Insert into DB (Replaces CSV appending)
        insert_weigh_in(date_str, weight_input)
        
        # 3. Feedback & Refresh
        st.sidebar.success("✅ Saved to Database!")
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# B. Load & Prep Data
df = load_data_from_db()

if df.empty:
    st.warning("⚠️ No data found. Start by logging your weight!")
    st.stop()

# Convert DB strings back to DateTime objects for Pandas math
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')
df['rolling_avg'] = df['weight'].rolling(window=7, min_periods=2).mean()

# C. Machine Learning (Linear Regression)
df['date_ordinal'] = df['date'].map(dt.datetime.toordinal)
X = df[['date_ordinal']]
y = df['weight']

model = LinearRegression()
model.fit(X, y)

# D. Calculations (The "Truth")
current_weight = df['weight'].iloc[-1]
actual_slope = model.coef_[0]

# Required Slope Math
status = "⚪ NO GOAL SET"
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

# 1. Actual Data
ax.scatter(df['date'], df['weight'], color='blue', alpha=0.6, label='Actual')

# 2. Trend Line
future_days = 14
last_date = df['date'].max()
future_dates = pd.date_range(start=df['date'].min(), end=last_date + pd.Timedelta(days=future_days))
future_ordinals = future_dates.map(dt.datetime.toordinal).values.reshape(-1, 1)
future_preds = model.predict(future_ordinals)

ax.plot(future_dates, future_preds, color='red', linestyle='--', label='Trend')

# 3. Ideal Path
if enable_goals:
    start_date = df['date'].iloc[0]
    start_weight = df['weight'].iloc[0]
    ax.plot([start_date, goal_date], [start_weight, goal_weight], color='green', linestyle=':', linewidth=2, label='Ideal')

# 4. Rolling Avg
ax.plot(df['date'], df['rolling_avg'], color='orange', linewidth=2, linestyle='--', label='7d Avg')

ax.set_title(f"Trajectory vs Goal")
ax.grid(True, linestyle=':', alpha=0.4)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.legend()
plt.xticks(rotation=45)

st.pyplot(fig)

# C. Raw Data Table
with st.expander("📄 View Raw Data"):
    clean_df = df[['date', 'weight']].copy()
    st.dataframe(clean_df.style.format({"date": lambda t: t.strftime("%Y-%m-%d"), "weight": "{:.1f}"}))

# DOWNLOAD BUTTON (In-Memory CSV Generation)
# We generate the CSV on the fly from the Database DataFrame
csv_buffer = clean_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label='💾 DOWNLOAD BACKUP CSV',
    data=csv_buffer,
    file_name='weight_winter.csv',
    mime='text/csv'
)
