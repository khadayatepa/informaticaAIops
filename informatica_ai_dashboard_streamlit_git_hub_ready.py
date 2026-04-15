import streamlit as st
import pandas as pd
import graphviz
from openai import OpenAI

# ------------------------------
# 1. Reality-Based Data Model
# ------------------------------
# In reality, one workflow has many sessions/tasks
workflow_hierarchy = {
    "wf_sales_daily": [
        {"task": "s_m_stage_orders", "type": "Session", "status": "SUCCESS", "src": "Oracle", "tgt": "Staging", "log": "Success"},
        {"task": "s_m_load_fact_sales", "type": "Session", "status": "FAILED", "src": "Staging", "tgt": "Snowflake", "log": "ORA-01653: unable to extend table SALES_FACT by 128 in tablespace USERS"},
        {"task": "cmd_gen_report", "type": "Command", "status": "NOT_STARTED", "src": "N/A", "tgt": "N/A", "log": "N/A"}
    ],
    "wf_cust_master": [
        {"task": "s_m_upsert_customers", "type": "Session", "status": "SUCCESS", "src": "SAP", "tgt": "MDM_Hub", "log": "Success"}
    ]
}

# ------------------------------
# 2. Logic: Automated Routing
# ------------------------------
def get_owner(log):
    if "ORA-" in log or "tablespace" in log.lower():
        return "DBA Team", "Storage/Database"
    elif "connection" in log.lower() or "network" in log.lower():
        return "Infra Team", "Connectivity"
    return "Informatica Dev", "Application/Logic"

# ------------------------------
# 3. UI Implementation
# ------------------------------
st.set_page_config(layout="wide", page_title="Infa AIOps")
st.title("🏭 Enterprise Informatica Observability")

selected_wf = st.selectbox("Select Workflow", list(workflow_hierarchy.keys()))
tasks = workflow_hierarchy[selected_wf]

# --- Metrics Section ---
failed_tasks = [t for t in tasks if t['status'] == 'FAILED']
c1, c2, c3 = st.columns(3)
c1.metric("Workflow Status", "FAILED" if failed_tasks else "SUCCESS", delta_color="inverse")
c2.metric("Total Tasks", len(tasks))
c3.metric("Critical Errors", len(failed_tasks))

# --- Visual Pipeline Layer ---
st.subheader("📍 Task Execution Lineage")
dot = graphviz.Digraph()
dot.attr(rankdir='LR')

# Build the chain of sessions
for i in range(len(tasks)):
    task = tasks[i]
    color = "green" if task['status'] == "SUCCESS" else "red" if task['status'] == "FAILED" else "grey"
    
    # Create Task Node
    dot.node(task['task'], f"{task['task']}\n({task['type']})", color=color, style="filled" if color != "grey" else "")
    
    # Connect to next task in workflow
    if i < len(tasks) - 1:
        dot.edge(task['task'], tasks[i+1]['task'])

st.graphviz_chart(dot)

# --- Session Detail & AI Debugger ---
st.subheader("🔍 Session-Level Investigation")
for task in tasks:
    with st.expander(f"{task['task']} - Status: {task['status']}"):
        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            st.write(f"**Source:** {task['src']}")
            st.write(f"**Target:** {task['tgt']}")
            if task['status'] == "FAILED":
                owner, category = get_owner(task['log'])
                st.error(f"Owner: {owner}")
                st.info(f"Category: {category}")
        
        with col_b:
            st.code(task['log'], language="sql")
            if task['status'] == "FAILED":
                st.button(f"Ask AI to Fix {task['task']}", key=task['task'])
