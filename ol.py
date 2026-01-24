import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt

d = pd.to_datetime("Jan 13 2025")
print(d)
df = d - dt.timedelta(days=14)
print(df)