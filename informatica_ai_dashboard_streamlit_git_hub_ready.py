import streamlit as st
import pandas as pd
import os
from openai import OpenAI

# ------------------------------
# UI: API Key Input
# ------------------------------
st.title("🚀 Informatica AI/ML Dashboard")

api_key = st.text_input("Enter OpenAI API Key", type="password")

client = None
if api_key:
    client = OpenAI(api_key=api_key)

# ------------------------------
# Sample Data (Replace with real logs)
# ------------------------------
workflow_data = [
    {"workflow": "wf_customer_load", "status": "FAILED", "duration": 300, "log": "ORA-00001 unique constraint violated"},
    {"workflow": "wf_orders_load", "status": "SUCCESS", "duration": 250, "log": "Completed successfully"},
    {"workflow": "wf_product_load", "status": "RUNNING", "duration": 100, "log": "Session running"},
]

df = pd.DataFrame(workflow_data)

# ------------------------------
# Filters
# ------------------------------
status_filter = st.selectbox("Filter by Status", ["ALL", "SUCCESS", "FAILED", "RUNNING"])

if status_filter != "ALL":
    df = df[df["status"] == status_filter]

# ------------------------------
# Metrics
# ------------------------------
st.subheader("📊 Workflow Metrics")
col1, col2, col3 = st.columns(3)

col1.metric("Total", len(df))
col2.metric("Success", len(df[df["status"] == "SUCCESS"]))
col3.metric("Failed", len(df[df["status"] == "FAILED"]))

# ------------------------------
# Data Table
# ------------------------------
st.subheader("📋 Workflow Details")
st.dataframe(df)

# ------------------------------
# AI Log Analysis
# ------------------------------
st.subheader("🧠 AI Log Analysis")

def analyze_with_ai(log):
    if not client:
        return "⚠️ Enter API Key to enable AI analysis"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an Informatica log analyzer."},
                {"role": "user", "content": f"Analyze this log and give root cause and fix: {log}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

for i, row in df.iterrows():
    st.markdown(f"### 🔹 {row['workflow']} ({row['status']})")
    result = analyze_with_ai(row['log'])
    st.write(result)

# ------------------------------
# Charts
# ------------------------------
st.subheader("📈 Status Distribution")
st.bar_chart(df["status"].value_counts())

# ==============================
# README.md (copy below into file)
# ==============================
"""
# Informatica AI Dashboard

## Features
- Workflow monitoring (Success/Failed/Running)
- AI-based log analysis using OpenAI
- Streamlit dashboard

## Setup
1. Clone repo
2. Install requirements:
   pip install -r requirements.txt
3. Run:
   streamlit run app.py

## Deploy on Streamlit Cloud
- Push to GitHub
- Connect repo in Streamlit Cloud

## Notes
- Enter OpenAI API key in UI
"""
