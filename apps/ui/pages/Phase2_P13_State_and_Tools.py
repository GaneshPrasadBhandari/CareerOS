import streamlit as st
import requests
import os

st.title("CareerOS Phase 2 — P13: State + Tool Registry")


API = os.getenv("CAREEROS_API_URL", "http://127.0.0.1:8000")


st.write("API Base:", API)

col1, col2 = st.columns(2)

with col1:
    if st.button("List Tools"):
        r = requests.get(f"{API}/tools", timeout=10)
        st.json(r.json())

with col2:
    if st.button("Init Run State"):
        payload = {"env": "dev", "orchestration_mode": "deterministic"}
        r = requests.post(f"{API}/runs/init", json=payload, timeout=10)
        st.json(r.json())
