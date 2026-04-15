import streamlit as st
import pandas as pd
import graphviz
from openai import OpenAI

# ------------------------------
# 1. Page Config & Professional Dark Theme
# ------------------------------
st.set_page_config(page_title="Informatica AIOps Control Center", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetric"] {
        background-color: #1e2130;
        border: 1px solid #3e4251;
        padding: 15px;
        border-radius: 10px;
    }
    div[data-testid="stMetricLabel"] { color: #00d4ff !important; font-weight: bold; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------
# 2. API Key & Global Title
# ------------------------------
st.title("🚀 Informatica AI Observability & Control Center")
api_key = st.text_input("🔑 Enter OpenAI API Key", type="password", help="Enables AI Diagnostics")
client = OpenAI(api_key=api_key) if api_key else None

# ------------------------------
# 3. Enterprise Data Model
# ------------------------------
all_workflows = [
    {
        "workflow": "wf_sales_ingestion",
        "status": "FAILED",
        "server": "INFA_PROD_01",
        "db": "SALES_DB",
        "duration": "15m",
        "tasks": [
            {"name": "s_m_stage", "status": "SUCCESS", "src": "Oracle_ERP", "tgt": "Staging_DB", "log": "Success"},
            {"name": "s_m_load_fact", "status": "FAILED", "src": "Staging_DB", "tgt": "Snowflake_DWH", "log": "ORA-01653: tablespace DATA_TS full"}
        ]
    },
    {
        "workflow": "wf_customer_sync",
        "status": "SUCCESS",
        "server": "INFA_PROD_02",
        "db": "CRM_DB",
        "duration": "5m",
        "tasks": [
            {"name": "s_m_upsert_cust", "status": "SUCCESS", "src": "Salesforce", "tgt": "Oracle_CRM", "log": "Success"}
        ]
    },
    {
        "workflow": "wf_inventory_update",
        "status": "FAILED",
        "server": "INFA_PROD_01",
        "db": "ERP_DB",
        "duration": "2m",
        "tasks": [
            {"name": "s_m_inv_fetch", "status": "FAILED", "src": "Kafka", "tgt": "ERP_STG", "log": "Connection timeout to Kafka:9092"}
        ]
    }
]

# ------------------------------
# 4. Global Filters & Top Metrics
# ------------------------------
st.divider()
view_filter = st.radio("🔍 Filter Environment View:", ["ALL", "FAILED", "SUCCESS"], horizontal=True)

# Apply Filter to Data
filtered_list = [wf for wf in all_workflows if view_filter == "ALL" or wf['status'] == view_filter]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Visible Workflows", len(filtered_list))
m2.metric("Failed Status", len([w for w in filtered_list if w['status']=="FAILED"]))
m3.metric("Infra Nodes", len(set(w['server'] for w in filtered_list)))
m4.metric("Environment", "PRODUCTION")

# ------------------------------
# 5. Visual Pipeline & AI Analysis (The Logic Layer)
# ------------------------------
st.subheader("📍 Workflow Infrastructure Trace")

if not filtered_list:
    st.info("No workflows found matching filter.")
else:
    for wf in filtered_list:
        # Expander acts as the "Dashboard" entry for each workflow
        with st.expander(f"Inspect: {wf['workflow']} | Server: {wf['server']} | Status: {wf['status']}", expanded=(wf['status']=="FAILED")):
            
            # --- Graphviz Visual Pipeline ---
            dot = graphviz.Digraph()
            dot.attr(rankdir='LR', bgcolor='transparent')
            
            for t in wf['tasks']:
                # Logic for Colors
                status_color = "#ff4b4b" if t['status'] == "FAILED" else "#00c853"
                line_color = "#ff4b4b" if t['status'] == "FAILED" else "#ffffff"
                
                # Icons via Shapes
                dot.node(f"src_{t['name']}", f"🗄️ {t['src']}\n(Source)", shape="database", color="#00d4ff", fontcolor="white", style="filled")
                dot.node(f"srv_{t['name']}", f"💻 {wf['server']}\n(Server)", shape="rectangle", color="#757575", fontcolor="white", style="filled")
                dot.node(t['name'], f"⚙️ {t['name']}\n({t['status']})", shape="component", color=status_color, fontcolor="white", style="filled")
                dot.node(f"tgt_{t['name']}", f"🎯 {t['tgt']}\n(Target)", shape="database", color=status_color if t['status']=="FAILED" else "#00c853", fontcolor="white", style="filled")
                
                # Connections [Fixed the line_col error here]
                dot.edge(f"src_{t['name']}", f"srv_{t['name']}", color="#ffffff")
                dot.edge(f"srv_{t['name']}", t['name'], color="#ffffff")
                dot.edge(t['name'], f"tgt_{t['name']}", color=line_color, penwidth="2.0")
            
            st.graphviz_chart(dot)
            
            # --- AI Root Cause & Team Responsibility ---
            if wf['status'] == "FAILED":
                for t in wf['tasks']:
                    if t['status'] == "FAILED":
                        # Automatic Routing Logic
                        team = "DBA TEAM" if "ORA-" in t['log'].upper() else "INFRA/APP TEAM"
                        st.error(f"❌ {t['name']} Failed | Assigned To: {team}")
                        st.code(f"Log Snippet: {t['log']}")
                        
                        if client:
                            if st.button(f"🤖 Get AI Fix: {t['name']}", key=f"ai_btn_{wf['workflow']}_{t['name']}"):
                                with st.spinner("AI analyzing logs..."):
                                    res = client.chat.completions.create(
                                        model="gpt-4o-mini",
                                        messages=[{"role": "user", "content": f"You are an Informatica Expert. Fix this for the {team}: {t['log']}"}]
                                    )
                                    st.success(res.choices[0].message.content)
            else:
                st.success("Lineage verified: All data successfully moved to target.")

# ------------------------------
# 6. Global Dashboard (Table & Charts)
# ------------------------------
st.divider()
st.subheader("📊 Global Environment Stats")

# Flatten data for the summary table
summary_df = pd.DataFrame([{
    "Workflow": w['workflow'],
    "Status": w['status'],
    "Server": w['server'],
    "Primary DB": w['db'],
    "Runtime": w['duration']
} for w in filtered_list])

col_tbl, col_cht = st.columns([2, 1])

with col_tbl:
    st.markdown("**All Workflow Metadata**")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

with col_cht:
    st.markdown("**Status Distribution**")
    if not summary_df.empty:
        st.bar_chart(summary_df['Status'].value_counts())
    else:
        st.write("No data for chart.")
