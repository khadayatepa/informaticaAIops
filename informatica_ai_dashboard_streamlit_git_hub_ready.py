import streamlit as st
import pandas as pd
import graphviz
from openai import OpenAI

# ------------------------------
# 1. Page Configuration & High-Visibility CSS
# ------------------------------
st.set_page_config(page_title="Informatica AIOps", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #1e2130;
        border: 1px solid #3e4251;
        padding: 15px;
        border-radius: 10px;
    }
    div[data-testid="stMetricLabel"] { color: #00d4ff !important; font-weight: bold; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    .main { background-color: #0e1117; }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------
# 2. Data Model (Multiple Workflows)
# ------------------------------
# In reality, workflows contain multiple sessions
all_workflows = [
    {
        "id": "wf_sales_daily",
        "status": "FAILED",
        "server": "INFA_NODE_01",
        "db": "SALES_DB",
        "integration": "Oracle Connector",
        "tasks": [
            {"name": "s_m_stage", "status": "SUCCESS", "log": "Success", "src": "Oracle", "tgt": "Staging"},
            {"name": "s_m_load", "status": "FAILED", "log": "ORA-01653: tablespace USERS full", "src": "Staging", "tgt": "Snowflake"}
        ]
    },
    {
        "id": "wf_cust_sync",
        "status": "SUCCESS",
        "server": "INFA_NODE_02",
        "db": "CRM_DB",
        "integration": "Salesforce API",
        "tasks": [
            {"name": "s_m_upsert", "status": "SUCCESS", "log": "Success", "src": "SFDC", "tgt": "Oracle"}
        ]
    },
    {
        "id": "wf_inventory_update",
        "status": "FAILED",
        "server": "INFA_NODE_01",
        "db": "ERP_DB",
        "integration": "Kafka Stream",
        "tasks": [
            {"name": "s_m_inv_fetch", "status": "FAILED", "log": "Connection timeout to Kafka broker", "src": "Kafka", "tgt": "Staging"}
        ]
    }
]

# ------------------------------
# 3. Sidebar & AI Setup
# ------------------------------
with st.sidebar:
    st.title("🛡️ Ops Control")
    api_key = st.text_input("OpenAI API Key", type="password")
    client = OpenAI(api_key=api_key) if api_key else None

def get_routing(log):
    if "ORA-" in log.upper(): return "DBA TEAM", "Database Issue"
    if "CONNECTION" in log.upper(): return "INFRA TEAM", "Network Issue"
    return "INFA TEAM", "Application Issue"

# ------------------------------
# 4. Multi-Workflow Filtering Logic
# ------------------------------
st.title("🚀 Informatica AI Observability")

# Global Filter Buttons
view_filter = st.radio("🔍 View Workflows By Status:", ["ALL", "FAILED", "SUCCESS"], horizontal=True)

# Filter logic
filtered_list = [wf for wf in all_workflows if view_filter == "ALL" or wf['status'] == view_filter]

# Metrics for the filtered set
m1, m2, m3 = st.columns(3)
m1.metric("Visible Workflows", len(filtered_list))
m2.metric("Total Failed", len([w for w in filtered_list if w['status'] == "FAILED"]))
m3.metric("Total Success", len([w for w in filtered_list if w['status'] == "SUCCESS"]))

st.divider()

# ------------------------------
# 5. Iterating through Multiple Workflows
# ------------------------------
if not filtered_list:
    st.info(f"No workflows found matching the '{view_filter}' status.")
else:
    for wf in filtered_list:
        # Create a header container for each workflow
        header_col, status_col = st.columns([4, 1])
        with header_col:
            st.subheader(f"📦 Workflow: {wf['id']}")
        with status_col:
            if wf['status'] == "FAILED":
                st.error("FAILED")
            else:
                st.success("SUCCESS")

        # Visual Pipeline for this specific workflow
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR', bgcolor='transparent', height='2')
        for i, t in enumerate(wf['tasks']):
            node_col = "#ff4b4b" if t['status'] == "FAILED" else "#00c853"
            dot.node(t['name'], f"{t['name']}\n({t['status']})", color=node_col, fontcolor="white", style="filled")
            if i < len(wf['tasks']) - 1:
                dot.edge(t['name'], wf['tasks'][i+1]['name'], color="white")
        st.graphviz_chart(dot)

        # Details expander for sessions
        with st.expander(f"View Session Details for {wf['id']}"):
            st.write(f"**Server:** {wf['server']} | **DB:** {wf['db']} | **Integration:** {wf['integration']}")
            for task in wf['tasks']:
                if task['status'] == "FAILED":
                    team, cat = get_routing(task['log'])
                    st.error(f"❌ {task['name']} - Assigned to: {team} ({cat})")
                    st.code(task['log'])
                    if client:
                        if st.button(f"Analyze {task['name']}", key=f"btn_{task['name']}"):
                            resp = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": f"Fix this Infa error: {task['log']}"}]
                            )
                            st.info(resp.choices[0].message.content)
                else:
                    st.success(f"✅ {task['name']} completed successfully.")
        
        st.markdown("---") # Separator between multiple workflows
