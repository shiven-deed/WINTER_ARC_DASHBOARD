import streamlit as st
from groq import Groq
import time

st.title("🔌 AI Connection Test")

try:
    api_key = st.secrets["GROQ_API_KEY"]
    st.success("✅ Secrets file found and API Key detected!")
except Exception as e:
    st.error(f"Error {e}")

client = Groq(api_key = api_key)
if st.button("Say 'hello' to the AI!"):
    with st.spinner("Connecting to AI"):
        time.sleep(3)
        try:
            completion = client.chat.completions.create(
                model = "llama-3.1-8b-instant",
                messages = [{'role' : 'user', 'content' : 'Hello! Are you online? Answer in one sentence.'}],
                temperature = 1,
                top_p = 1,
                max_tokens = 1024,
                stream = False,
                stop = None
            )

            response = completion.choices[0].message.content

            st.info(f"🤖 AI Says: {response}")
        except Exception as e:
            st.error(f"Error {e}")