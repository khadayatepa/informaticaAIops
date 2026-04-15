import streamlit as st
import pandas as pd
import graphviz
from openai import OpenAI

# ------------------------------
# 1. Page Config & Professional Dark Theme
# ------------------------------
st.set_page_config(page_title="Informatica AIOps", layout="wide")

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
    .stTable { background-color: #1e2130; color: white; }
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
            {"name": "s_m_inv_fetch", "status": "FAILED", "src": "Kafka", "tgt": "ERP_STG", "log": "Connection timeout to Kafka broker:9092"}
        ]
    }
]

# ------------------------------
# 4. Global Filters & Metrics
# ------------------------------
st.divider()
view_filter = st.radio("🔍 Filter View:", ["ALL", "FAILED", "SUCCESS"], horizontal=True)
filtered_list = [wf for wf in all_workflows if view_filter == "ALL" or wf['status'] == view_filter]

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Visible Workflows", len(filtered_list))
m2.metric("Failed Status", len([w for w in filtered_list if w['status']=="FAILED"]))
m3.metric("Infra Nodes", len(set(w['server'] for w in filtered_list)))
m4.metric("Environment", "PROD")

# ------------------------------
# 5. Visual Pipeline & AI Analysis
# ------------------------------
st.subheader("📍 Workflow Infrastructure Trace")

if not filtered_list:
    st.info("No workflows found matching filter.")
else:
    for wf in filtered_list:
        with st.expander(f"Inspect: {wf['workflow']} ({wf['status']})", expanded=(wf['status']=="FAILED")):
            # Lineage with Icons
            dot = graphviz.Digraph()
            dot.attr(rankdir='LR', bgcolor='transparent')
            
            for t in wf['tasks']:
                status_color = "#ff4b4b" if t['status'] == "FAILED" else "#00c853"
                line_color = "#ff4b4b" if t['status'] == "FAILED" else "#ffffff"
                
                dot.node(f"src_{t['name']}", f"🗄️ {t['src']}\n(Source)", shape="database", color="#00d4ff", fontcolor="white", style="filled")
                dot.node(f"srv_{t['name']}", f"💻 {wf['server']}\n(Informatica)", shape="rectangle", color="#757575", fontcolor="white", style="filled")
                dot.node(t['name'], f"⚙️ {t['name']}\n({t['status']})", shape="component", color=status_color, fontcolor="white", style="filled")
                dot.node(f"tgt_{t['name']}", f"🎯 {t['tgt']}\n(Target)", shape="database", color=status_color if t['status']=="FAILED" else "#00c853", fontcolor="white", style="filled")
                
                dot.edge(f"src_{t['name']}", f"srv_{t['name']}", color="#ffffff")
                dot.edge(f"srv_{t['name']}", t['name'], color="#ffffff")
                dot.edge(t['name'], f"tgt_{t['name']}", color=line_col, penwidth="2.0")
            
            st.graphviz_chart(dot)
            
            # AI Diagnostics
            if wf['status'] == "FAILED":
                for t in wf['tasks']:
                    if t['status'] == "FAILED":
                        team = "DBA TEAM" if "ORA-" in t['log'] else "INFRA/APP TEAM"
                        st.error(f"Issue found in {t['name']} | Responsible: {team}")
                        st.code(t['log'])
                        if client:
                            if st.button(f"Analyze with AI: {t['name']}", key=f"ai_{wf['workflow']}_{t['name']}"):
                                res = client.chat.completions.create(
                                    model="gpt-4o-mini",
                                    messages=[{"role": "user", "content": f"Provide root cause and fix for {team}: {t['log']}"}]
                                )
                                st.info(res.choices[0].message.content)

# ------------------------------
# 6. Missing Dashboard (Table & Charts)
# ------------------------------
st.divider()
st.subheader("📋 Global Workflow Dashboard")

# Convert to flat table for the dashboard view
flat_data = []
for wf in all_workflows:
    flat_data.append({
        "Workflow": wf['workflow'],
        "Status": wf['status'],
        "Infa Server": wf['server'],
        "DB Name": wf['db'],
        "Duration": wf['duration']
    })
df_full = pd.DataFrame(flat_data)

tab1, tab2 = st.tabs(["Data Table", "Distribution Chart"])

with tab1:
    st.dataframe(df_full, use_container_width=True)

with tab2:
    chart_data = df_full['Status'].value_counts()
    st.bar_chart(chart_data)
