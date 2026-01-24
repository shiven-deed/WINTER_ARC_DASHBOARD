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
from groq import Groq
from db import (
    init_db,
    insert_or_update_log,
    load_all_logs,
    delete_log,
    delete_all
)
# GETTING API KEY
import os

groq = os.getenv('GROQ_API_KEY')
if not groq: 
    st.error("❌ ERROR: GROQ_API_KEY missing.")
    st.stop()

st.set_page_config(page_title="WINTER ARC DASHBOARD", layout="centered")
st.title("❄️ WINTER ARC")

init_db()

def get_ai_response(user_prompt, coach_mode, days_since_log, weight_change):
    api = groq
    try:
        client = Groq(api_key=api)

        # --- LOGIC SPLIT ---
        if coach_mode == "BAD":
            # LAZY MODE (User hasn't logged)
            system_prompt = f"""
            ROLE: Ruthless Military Drill Sergeant.
            TASK: The recruit has been AWOL (absent) for {days_since_log} days.
            
            INSTRUCTION:
            1. Do NOT look at weight data.
            2. Viciously insult their lack of discipline for disappearing.
            3. Command them to log immediately.
            4. STRICT LIMIT: Maximum 25 words. No filler.
            """
        else:
            # CONSISTENT MODE (User logged recently)
            # Python determines the status, AI provides the roast
            if weight_change > 0:
                tone = "Vicious, demeaning, angry."
                action = f"They GAINED {weight_change:.2f}kg. Shame them for being weak and eating too much."
            elif weight_change == 0:
                 tone = "Mocking, sarcastic."
                 action = "They stagnated (0kg change). Mock them for wasting time."
            else:
                tone = "Grudging respect but paranoid."
                action = f"They LOST {abs(weight_change):.2f}kg. Acknowledge it briefly, but warn them not to get soft or arrogant."

            system_prompt = f"""
            ROLE: Ruthless Winter Arc Coach. 
            TONE: {tone}
            
            DATA: {action}

            INSTRUCTION:
            1. State the weight change explicitly (e.g., "You gained 0.4kg...").
            2. Follow immediately with a high-quality insult or warning based on the TONE above.
            3. NO encouragement. NO "keep going". NO generic advice.
            4. STRICT LIMIT: Maximum 30 words.
            """

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8, # Slightly lower to keep them focused on the insult
            max_tokens=100,
        )
        return completion.choices[0].message.content

    except Exception as e:
        return f"Coach is offline: {e}"
# ==========================================
# 2. SIDEBAR (INPUTS)
# ==========================================
st.sidebar.header("📝 LOG DATA")
with st.sidebar.form("entry_form"):
    weight_input = st.number_input("Weight (kg):", step=0.1, format="%.1f", value = 80.0)
    date_input = st.date_input("Date:", value=dt.date.today())
    submit_log = st.form_submit_button("LOG ENTRY")
    if date_input > pd.Timestamp.now().date():
        st.sidebar.error(f"⚠️ REJECTED: {date_input} is of the future. Check input.")
    if weight_input < 40 or weight_input > 150:
        st.sidebar.error(f"⚠️ REJECTED: {weight_input}kg is unlikely. Check input.")

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
    if 40 <= weight_input <= 150 and date_input <= pd.Timestamp.now().date():
        try:
            insert_or_update_log(date_input, weight_input)
            st.sidebar.success("✅ Saved to SQL")
            time.sleep(0.5)

        except Exception as e:
            st.sidebar.error(f"Error: {e}")

        st.rerun()
# B. Load & Prep Data
try:
    df = load_all_logs()
    if df.empty:
        st.warning("⚠️ Database is empty. Log your first weight!")
        st.stop()

    df['date'] = pd.to_datetime(df['date'])
    df['rolling_avg'] = df['weight'].rolling(window = 7, min_periods = 2).mean()

except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop() # Stop execution here if no data

# GROQ CONTEXT
# 1. LAST LOG DIFF
n = len(df)
if n>0:
    last_log = pd.to_datetime(df['date']).max().normalize()
    today = pd.Timestamp.now().normalize()
    days_since_log = (today - last_log).days
    if days_since_log > 3:
        coach_mode = "BAD"
    else:
        coach_mode = "GOOD"
else:
    days_since_log = 0
# 2. TOTAL LOSS IN WEIGHT
weekly_avg = df['weight'].tail(7).mean() if n >= 2 else df['weight'].iloc[-1]
last_w = df['weight'].iloc[-1]
prev_w = df['weight'].iloc[-2] if n>=2 else last_w
prev_2w = df['weight'].iloc[-3] if n>=3 else prev_w
delta_prev = prev_w - prev_2w
delta_last = last_w - prev_w
net_3 = last_w - prev_2w
deviation_7 = last_w - weekly_avg # positive = good


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
ax.scatter(df['date'], df['weight'], color='blue', alpha=0.6, label='Reality')

# 2. Trend Line (Red Dashed) - Projected 14 Days
future_days = 14
last_date = df['date'].max()
future_dates = pd.date_range(start=df['date'].min(), end=last_date + pd.Timedelta(days=future_days))
future_ordinals = future_dates.map(dt.datetime.toordinal).values.reshape(-1, 1)
future_preds = model.predict(future_ordinals)

ax.plot(future_dates, future_preds, alpha = 0.8, color='red', linestyle='--', label='Trend')

# 3. Ideal Path (Green Dashed) - Only if Goal Enabled
if enable_goals:
    start_date = df['date'].iloc[0]
    start_weight = df['weight'].iloc[0]
    ax.plot([start_date, goal_date], [start_weight, goal_weight], color='green', alpha = 0.8, linestyle=':', linewidth=2, label='Ideal')
# 4. ROLLING AVG(ORANGE DASHED)
ax.plot(df['date'], df['rolling_avg'], alpha = 1, color = 'orange', linewidth = 2, linestyle = '-', label = 'smoothing')

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
    if min_date <= start_date and end_date <= max_date and start_date < end_date:    
        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date) # MASKING FOR FILTER
        filtered_date = df.loc[mask][['date', 'weight']]
        st.write(f"Showing {len(filtered_date)} entries: ") # DISPLAY
        st.dataframe(filtered_date.style.format({'date': lambda x: x.strftime("%Y-%m-%d"), 'weight': '{:.1f}'}))
    else:
        st.error("Invalid Date Range!!")

    # B. DELETE INTERFACE
    delete_option = (df.apply(lambda x: f"{x['date'].strftime("%Y-%m-%d")} | {x['weight']}", axis = 1)).to_list()[::-1]
    selected_option = st.selectbox(
            "Select entry to delete: ",
            options = delete_option,
            index= None,
            placeholder = "Select an entry ..."
    )
    if selected_option:
        if st.button(f"🗑️ PERMANENTLY DELETE {selected_option.split(" | ")[0]}"):
            delete_key = selected_option.split(" | ")[0]

            try:
                delete_log(delete_key)
                time.sleep(1)
                st.success(f"✅ Deleted entry for {delete_key}")
            except Exception as e:
                st.error(f"Could not delete {selected_option}: {e}")

            st.rerun() # Refresh to update graph and remove from list
    

# AI GROQ CALLING
st.sidebar.divider()
st.sidebar.header("🤖 WINTER ARC COACH")

user_query = st.sidebar.text_area("Enter the prompt: ")

if st.sidebar.button("GET HELP..."):
    if user_query:
        with st.sidebar.status("Connecting to Groq...") as status:
            time.sleep(2)
            response = get_ai_response(user_query, coach_mode, days_since_log, delta_last)
            st.sidebar.info(response)
            status.update(label = "RESPONSE READY", state = "complete")
    else:
        st.sidebar.warning("You must say something first.")


# DOWNLOAD BUTTON
clean_df = df[['date', 'weight']].copy()
download = clean_df.to_csv(index = False).encode('utf-8')

st.download_button(
    label = '💾 DOWNLOAD BACKUP CSV',
    data = download,
    file_name = 'weight_winter.csv',
    mime = 'text/csv'
)
if st.button("DELETE ALL DATA"):
    try: 
        delete_all()
        time.sleep(1)
        st.success(f"✅ Deleted all entries")
    except Exception as e:
        st.error(f"Could not delete, ERROR: {e}")
    st.rerun()