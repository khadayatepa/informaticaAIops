import streamlit as st
import pandas as pd
import graphviz
from openai import OpenAI

# ------------------------------
# Configuration & Styling
# ------------------------------
st.set_page_config(page_title="Informatica AI Observability", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------
# Enhanced Metadata (The "Truth" Layer)
# ------------------------------
# In a real app, this would come from Informatica Repository Views (REP_WFLOW_RUN, etc.)
workflow_data = [
    {
        "workflow": "wf_customer_sync",
        "status": "FAILED",
        "duration": "5m 20s",
        "source": "Oracle_CRM",
        "target": "Snowflake_DWH",
        "server": "INFA_PROD_01",
        "db_name": "CRM_PROD",
        "integration": "Salesforce API",
        "log": "ORA-01555: snapshot too old: rollback segment number 9 with name 'RBS09' too small",
        "stage_failed": "Source Fetch"
    },
    {
        "workflow": "wf_order_ingestion",
        "status": "SUCCESS",
        "duration": "12m 45s",
        "source": "SAP_ERP",
        "target": "S3_Data_Lake",
        "server": "INFA_PROD_02",
        "db_name": "HANA_DB",
        "integration": "Kafka (Orders Stream)",
        "log": "Workflow completed successfully.",
        "stage_failed": None
    },
    {
        "workflow": "wf_inventory_update",
        "status": "FAILED",
        "duration": "1m 10s",
        "source": "MySQL_Store",
        "target": "Oracle_ERP",
        "server": "INFA_PROD_01",
        "db_name": "STORE_DB",
        "integration": "Local Filesystem",
        "log": "SF_34038: Client side error [Connection timed out]",
        "stage_failed": "Integration Service"
    }
]

df = pd.DataFrame(workflow_data)

# ------------------------------
# Logic: Ownership & Failure Mapping
# ------------------------------
def get_ownership(log):
    log = log.upper()
    if "ORA-" in log or "DB" in log:
        return "DBA Team", "🔴 Database Issue"
    if "CONNECTION" in log or "TIMEOUT" in log or "SF_" in log:
        return "Infra/Network Team", "🟡 Connectivity/Server Issue"
    if "UNIQUE CONSTRAINT" in log or "DATA TYPE" in log:
        return "App/Dev Team", "🔵 Data Quality Issue"
    return "Informatica Admin", "🟣 Session/Service Issue"

# ------------------------------
# Sidebar & Auth
# ------------------------------
with st.sidebar:
    st.title("🛡 Ops Settings")
    api_key = st.text_input("OpenAI API Key", type="password")
    st.divider()
    st.info("This dashboard maps Informatica Metadata to AI Root Cause Analysis.")

client = OpenAI(api_key=api_key) if api_key else None

# ------------------------------
# UI: Header & Metrics
# ------------------------------
st.title("🚀 Informatica AI/ML Observability Platform")
st.markdown("---")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Jobs", len(df))
m2.metric("Failed", len(df[df['status'] == 'FAILED']), delta_color="inverse")
m3.metric("Active Servers", df['server'].nunique())
m4.metric("Active DBs", df['db_name'].nunique())

# ------------------------------
# Visual Pipeline (Lineage)
# ------------------------------
st.subheader("🔗 End-to-End Visual Pipeline")

selected_wf = st.selectbox("Select Workflow to Trace", df['workflow'].tolist())
row = df[df['workflow'] == selected_wf].iloc[0]

# Generate DAG using Graphviz
dot = graphviz.Digraph(comment='Lineage')
dot.attr(rankdir='LR', size='10,5')

# Nodes
dot.node('S', f"SOURCE: {row['source']}\n({row['db_name']})", shape='database', color='blue')
dot.node('I', f"SERVER: {row['server']}\n(Informatica)", shape='rectangle')
dot.node('T', f"TARGET: {row['target']}", shape='database', color='green')

# Logic for failure coloring
edge_color = "black"
if row['status'] == "FAILED":
    edge_color = "red"
    if "Source" in str(row['stage_failed']):
        dot.node('S', color='red', style='filled')
    else:
        dot.node('I', color='red', style='filled')

dot.edge('S', 'I', label=f"via {row['integration']}", color=edge_color)
dot.edge('I', 'T', color=edge_color)

st.graphviz_chart(dot)

# ------------------------------
# AI Analysis & Responsibility
# ------------------------------
st.subheader("🧠 Incident Intelligence")

col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown(f"### Log Analysis: {selected_wf}")
    if row['status'] == "SUCCESS":
        st.success("Workflow is healthy. No action required.")
    else:
        owner, issue_type = get_ownership(row['log'])
        st.error(f"**Issue Type:** {issue_type}")
        st.warning(f"**Assigned To:** {owner}")
        
        if client:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an Informatica Expert. Analyze the log, provide a technical root cause, and a step-by-step fix."},
                        {"role": "user", "content": f"Log: {row['log']}\nSource: {row['source']}\nTarget: {row['target']}"}
                    ]
                )
                st.markdown("#### AI Root Cause & Fix")
                st.write(response.choices[0].message.content)
            except Exception as e:
                st.write(f"AI Analysis unavailable: {e}")
        else:
            st.info("💡 Provide an API Key in the sidebar for AI-powered fixes.")

with col_right:
    st.markdown("### System Context")
    st.json({
        "Integration": row['integration'],
        "Server": row['server'],
        "DB Name": row['db_name'],
        "Duration": row['duration']
    })

# ------------------------------
# Global Infrastructure View
# ------------------------------
st.divider()
st.subheader("📊 Global Status Table")
st.dataframe(df[['workflow', 'status', 'source', 'target', 'server', 'db_name', 'integration']], use_container_width=True)
