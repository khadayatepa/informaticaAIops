import streamlit as st
import pandas as pd
import graphviz
from openai import OpenAI

# ------------------------------
# 1. Page Configuration & VISIBILITY FIX
# ------------------------------
st.set_page_config(page_title="Informatica AIOps Observability", layout="wide")

# Enhanced CSS for High-Visibility in Dark Mode
st.markdown("""
    <style>
    /* Main Background */
    .main { background-color: #0e1117; color: white; }
    
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #1e2130;
        border: 1px solid #3e4251;
        padding: 15px 20px;
        border-radius: 10px;
        color: white; /* Forces overall text to white */
    }

    /* Specifically targeting Metric Labels and Values for visibility */
    div[data-testid="stMetricLabel"] {
        color: #ccd0d9 !important; /* Light grey for labels */
        font-size: 1rem !important;
    }
    
    div[data-testid="stMetricValue"] {
        color: #ffffff !important; /* Pure white for values */
        font-weight: bold !important;
    }

    /* Expander Styling */
    .streamlit-expanderHeader {
        background-color: #1e2130;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------
# 2. Reality-Based Data Model
# ------------------------------
workflow_data = {
    "wf_sales_ingestion_daily": {
        "server": "INFA_PROD_NODE_01",
        "db_name": "SALES_DB",
        "integration": "Kafka + Oracle Connection",
        "tasks": [
            {"task": "s_m_pre_check", "type": "Command", "status": "SUCCESS", "log": "Script success", "src": "N/A", "tgt": "N/A"},
            {"task": "s_m_load_stg_sales", "type": "Session", "status": "SUCCESS", "log": "Success", "src": "Oracle_Prod", "tgt": "Staging_DB"},
            {"task": "s_m_transform_fact", "type": "Session", "status": "FAILED", "log": "ORA-01653: unable to extend table SALES.FACT_SALES by 128 in tablespace DATA_TS", "src": "Staging_DB", "tgt": "Snowflake_DWH"},
            {"task": "s_m_post_cleanup", "type": "Session", "status": "NOT_STARTED", "log": "N/A", "src": "N/A", "tgt": "N/A"}
        ]
    }
}

# ------------------------------
# 3. Sidebar & API Key
# ------------------------------
with st.sidebar:
    st.title("🛡️ Ops Control")
    api_key = st.text_input("OpenAI API Key", type="password")
    client = OpenAI(api_key=api_key) if api_key else None

# ------------------------------
# 4. Main UI
# ------------------------------
st.title("🚀 Informatica AI Observability")

selected_wf_name = st.selectbox("Select Workflow", list(workflow_data.keys()))
wf_details = workflow_data[selected_wf_name]
tasks = wf_details['tasks']

# --- KPI Row (Now with Fixed Visibility) ---
failed_tasks = [t for t in tasks if t['status'] == 'FAILED']
m1, m2, m3, m4 = st.columns(4)

# Status logic for delta color
status_val = "FAILED" if failed_tasks else "HEALTHY"
m1.metric("Workflow Status", status_val)
m2.metric("Total Tasks", len(tasks))
m3.metric("Infra Node", wf_details['server'])
m4.metric("Target DB", wf_details['db_name'])

# --- Visual Pipeline ---
st.subheader("🔄 Visual Pipeline")
dot = graphviz.Digraph()
dot.attr(rankdir='LR', bgcolor='transparent')

for i, task in enumerate(tasks):
    node_color = "#ff4b4b" if task['status'] == "FAILED" else "#00c853" if task['status'] == "SUCCESS" else "#757575"
    dot.node(task['task'], f"{task['task']}\n({task['type']})", 
             color=node_color, fontcolor='white', style='filled', shape='box')
    
    if i < len(tasks) - 1:
        dot.edge(task['task'], tasks[i+1]['task'], color="#ffffff")

st.graphviz_chart(dot)

# --- Task Details ---
st.subheader("📋 Session Investigation")
for task in tasks:
    with st.expander(f"{task['task']} - {task['status']}"):
        st.write(f"**Source:** {task['src']} | **Target:** {task['tgt']}")
        st.code(task['log'], language="log")
