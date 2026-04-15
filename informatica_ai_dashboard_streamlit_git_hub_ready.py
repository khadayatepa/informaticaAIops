import streamlit as st
import pandas as pd
import graphviz
from openai import OpenAI

# ------------------------------
# 1. Page Configuration
# ------------------------------
st.set_page_config(page_title="Informatica AIOps Observability", layout="wide")

# Custom CSS for a professional "Dark Mode" look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4251; }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------
# 2. The "Real-World" Metadata Model
# ------------------------------
# Hierarchical data: One Workflow -> Multiple Sessions/Tasks
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
    },
    "wf_customer_master_sync": {
        "server": "INFA_PROD_NODE_02",
        "db_name": "CRM_PROD",
        "integration": "Salesforce REST API",
        "tasks": [
            {"task": "s_m_upsert_cust", "type": "Session", "status": "SUCCESS", "log": "Success", "src": "Salesforce", "tgt": "Oracle_CRM"}
        ]
    }
}

# ------------------------------
# 3. Intelligence Logic
# ------------------------------
def classify_and_route(log):
    log_upper = log.upper()
    if "ORA-" in log_upper or "TABLESPACE" in log_upper:
        return "DBA TEAM", "🔴 Database Storage/Permission", "Request Tablespace Expansion"
    if "CONNECTION" in log_upper or "TIMEOUT" in log_upper:
        return "INFRA TEAM", "🟡 Network/Connectivity", "Check Firewall/VPN Tunnel"
    if "UNIQUE CONSTRAINT" in log_upper or "DATA TYPE" in log_upper:
        return "APP DEV TEAM", "🔵 Data Integrity", "Validate Source Data Quality"
    return "INFORMATICA ADMIN", "🟣 Service/Engine", "Restart Integration Service"

# ------------------------------
# 4. Sidebar & API Key
# ------------------------------
with st.sidebar:
    st.title("🛡️ Ops Control Center")
    api_key = st.text_input("OpenAI API Key", type="password", help="Enter key to enable AI Root Cause Analysis")
    st.divider()
    st.info("This platform provides lineage and ownership mapping for Informatica PowerCenter/IICS.")

client = OpenAI(api_key=api_key) if api_key else None

# ------------------------------
# 5. Main Dashboard UI
# ------------------------------
st.title("🚀 Informatica AI Observability & AIOps")
st.markdown("---")

# Selection
selected_wf_name = st.selectbox("Select Workflow to Inspect", list(workflow_data.keys()))
wf_details = workflow_data[selected_wf_name]
tasks = wf_details['tasks']

# --- KPI Row ---
failed_tasks = [t for t in tasks if t['status'] == 'FAILED']
m1, m2, m3, m4 = st.columns(4)
m1.metric("Workflow Status", "FAILED" if failed_tasks else "HEALTHY", delta_color="inverse")
m2.metric("Total Tasks", len(tasks))
m3.metric("Infra Node", wf_details['server'])
m4.metric("Target DB", wf_details['db_name'])

# --- Visual Pipeline (Lineage) ---
st.subheader("🔄 Visual Pipeline & Failure Point")
dot = graphviz.Digraph()
dot.attr(rankdir='LR', bgcolor='transparent')

for i, task in enumerate(tasks):
    color = "green" if task['status'] == "SUCCESS" else "red" if task['status'] == "FAILED" else "gray"
    # Node represents the Session
    dot.node(task['task'], f"{task['task']}\n({task['type']})", color=color, fontcolor='white', style='filled')
    
    # Edge represents the sequence
    if i < len(tasks) - 1:
        next_task = tasks[i+1]['task']
        dot.edge(task['task'], next_task, color="white")

st.graphviz_chart(dot)

# --- Task Details & AI Analysis ---
st.subheader("📋 Session-Level Deep Dive")

for task in tasks:
    status_icon = "✅" if task['status'] == "SUCCESS" else "❌" if task['status'] == "FAILED" else "⏳"
    with st.expander(f"{status_icon} {task['task']} - {task['status']}"):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**System Metadata**")
            st.write(f"🔹 **Source:** `{task['src']}`")
            st.write(f"🔹 **Target:** `{task['tgt']}`")
            st.write(f"🔹 **Integration:** `{wf_details['integration']}`")
            
            if task['status'] == "FAILED":
                team, category, action = classify_and_route(task['log'])
                st.error(f"**Responsible:** {team}")
                st.warning(f"**Root Cause:** {category}")
                st.info(f"**Next Step:** {action}")
        
        with col2:
            st.markdown("**Execution Log Snippet**")
            st.code(task['log'], language="log")
            
            if task['status'] == "FAILED":
                if client:
                    if st.button(f"Analyze with AI", key=f"btn_{task['task']}"):
                        with st.spinner("AI Consulting Informatica Knowledge Base..."):
                            response = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[
                                    {"role": "system", "content": "You are an Informatica + Oracle DBA expert. Provide a technical root cause and a clear solution."},
                                    {"role": "user", "content": f"Session {task['task']} failed in Informatica. Log: {task['log']}"}
                                ]
                            )
                            st.markdown("### 🤖 AI Recommendation")
                            st.success(response.choices[0].message.content)
                else:
                    st.caption("Provide OpenAI Key in sidebar to unlock AI Fixes.")

# --- Bottom Data View ---
st.divider()
st.subheader("📊 Raw Workflow Metadata")
st.dataframe(pd.DataFrame(tasks), use_container_width=True)
