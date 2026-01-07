import streamlit as st
import pandas as pd

df = pd.read_csv("weight_log.csv")
delete = (df.apply(lambda x: f"Select {x['date']} | {x['weight']}", axis =1)).to_list()[::-1]
print(delete)