import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import time
from sklearn.linear_model import LinearRegression

# 1. LAYOUT
st.set_page_config(page_title = "WINTER ARC DASHBOARD", layout = "centered")

st.title("WINTER ARC")

# 2. Data Loading
try:
    df = pd.read_csv("weight_log.csv")
    df['date'] = pd.to_datetime(df['date'])
    st.write("Data Loaded")
    display_df = df.copy()
    display_df['date'] = display_df['date'].dt.date
    st.dataframe(display_df)
except:
    st.error("Data not loaded!!")

# Day 2: New data
# A . SIDEBAR
st.sidebar.header("LOG DATA")
# B. FORM
with st.sidebar.form("entry form"):
    weight = st.number_input("Enter weight: ", step = 0.1, format = "%.f")
    date = st.date_input("Enter date: ")
    submitted = st.form_submit_button("SUBMIT")
# C. DATA READING
if submitted:
    try:
        new = pd.DataFrame({'weight' : [weight], 'date' : [pd.to_datetime(date)]})
        df = pd.concat([df, new], ignore_index = True)
        df.to_csv("weight_log.csv", index = False)
        st.sidebar.success("Data Recorded")
        time.sleep(2)
    except:
        st.sidebar.error("Data not recorded!!")

    st.rerun()

# D. MODEL
df['date_ordinal'] = df['date'].map(dt.datetime.toordinal)
x = df[['date_ordinal']]
y = df['weight']
model = LinearRegression()
model.fit(x,y)

# Day 3: VISUALS ORACLE
st.header("The Visual Oracle")

# Establshing future days
future_days = 14
last_date = df['date'].max()
future_date = pd.date_range(start = df['date'].min(), end = last_date + pd.Timedelta(days = future_days))

# Dataframe for future Prediction
future_df = pd.DataFrame({'date' : future_date})
future_df['date_ordinal'] = future_df['date'].map(dt.datetime.toordinal)  # for ML model 
future_df['predicted'] = model.predict(future_df[['date_ordinal']])

# PLOT
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

fig, ax = plt.subplots(figsize = (10,5))

# PLOT A. SCATTER BLUE ACTUAL DATA
ax.scatter(df['date'], df['weight'], color = 'blue', label = 'Actual Weigh-in', zorder = 5)

# PLOT B. PLOT RED PREDICTED DATA
ax.plot(future_df['date'], future_df['predicted'], color = 'red', label = 'Trend Weigh-in', linestyle = '--')

# PLOT C. VISUALS
ax.set_title(f"Weight Trend Projection (+{future_days}days)")  #TITLE
ax.set_ylabel("Weight (kg)")  # Y AXIS LABELING
ax.grid(True, linestyle = ':', alpha = 0.6)
ax.legend()

ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
plt.xticks(rotation = 45)

st.pyplot(fig)

# E. PREDICTION
current_date = df['date'].max()
future_date = current_date + dt.timedelta(days = future_days)
future_ordinal = np.array([[future_date.toordinal()]])
# F. DISPLAY
current_weight = df['weight'].iloc[-1]
future_weight = model.predict(future_ordinal)[0]
# 4. FINAL DISPLAY
st.divider()

col1,col2,col3 = st.columns(3)
col1.metric("Current Weight",f"{current_weight: .1f} kg")
col2.metric("Predicted Weight", f"{future_weight: .1f} kg")
if future_weight < current_weight:
    col3.success("Status : ON TRACK")
else:
    col3.error("Status : OFF TRACK")