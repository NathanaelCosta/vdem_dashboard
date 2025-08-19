import streamlit as st, sys, pandas as pd, platform
st.set_page_config(page_title="Health", layout="centered")
st.title("✅ Health Check")
st.write("Python:", sys.version)
st.write("Platform:", platform.platform())
st.write("Pandas:", pd.__version__)
st.success("App mínimo rodando.")