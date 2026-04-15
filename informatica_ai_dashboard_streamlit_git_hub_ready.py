import streamlit as st
import pandas as pd
import graphviz
from openai import OpenAI

# ------------------------------
# 1. Page Config & High-Visibility CSS
# ------------------------------
st.set_page_config(page_title="Informatica AIOps", layout="wide")

st.markdown("""
    <style>
    /* Force high visibility for Metric Cards in Dark Mode */
    div[data-testid="stMetric"] {
        background-color: #1e2130;
        border: 1px solid #3e4251;
        padding: 15px;
        border-radius: 10px;
    }
    div[data-testid="stMetricLabel"] {
        color: #00d4ff !important; /* Bright Cyan for Labels */
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff !important; /* Pure White for Values */
    }
    /* Style for the selectbox to make it stand out */
    .stSelectbox label {
        color: #ffffff !important;
        font-size: 1.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------
# 2. Production Metadata Model
# ------------------------------
# Mapping real Informatica hierarchy: Workflow -> Sessions
raw_data = {
    "wf_sales_daily": {
        "status": "FAILED",
        "server": "INFA_NODE_01",
        "db": "SALES_DB",
        "tasks": [
            {"name": "s_m_stage", "status": "SUCCESS", "log": "Success", "src": "Oracle", "tgt": "Staging"},
            {"name": "s_m_load", "status": "FAILED", "log": "ORA-01653: tablespace full", "src": "Staging", "tgt": "Snowflake"}
        ]
    },
    "wf_cust_sync": {
        "status": "SUCCESS",
        "server": "INFA_NODE_02",
        "db": "CRM_DB",
        "tasks": [
            {"name": "s_m_upsert", "status": "SUCCESS", "log": "Success", "src": "SAP", "tgt": "Oracle"}
        ]
    }
}

# ------------------------------
# 3. Sidebar & Logic
# ------------------------------
with st.sidebar:
    st.title("🛡️ Controls")
    api_key = st.text_input("OpenAI Key", type="password")
    client = OpenAI(api_key=api_key) if api_key else None

def get_routing(log):
    if "ORA-" in log.upper(): return "DBA TEAM", "Database Issue"
    return "INFA TEAM", "Application Issue"

# ------------------------------
# 4. Filter Logic (THE KEY FEATURE)
# ------------------------------
st.title("🚀 Informatica AI Observability")

# This creates the filter you asked for
view_filter = st.radio("🔍 Filter Dashboard By Status:", ["ALL", "FAILED", "SUCCESS"], horizontal=True)

# Filter the workflow list based on selection
filtered_wfs = {k: v for k, v in raw_data.items() if view_filter == "ALL" or v['status'] == view_filter}

if not filtered_wfs:
    st.warning(f"No Workflows found with status: {view_filter}")
else:
    # Top Metrics for the Filtered View
    m1, m2, m3 = st.columns(3)
    m1.metric("Workflows Visible", len(filtered_wfs))
    m2.metric("Total Sessions", sum(len(v['tasks']) for v in filtered_wfs.values()))
    m3.metric("Selected View", view_filter)

    st.divider()

    # ------------------------------
    # 5. Visual Pipeline & Detail View
    # ------------------------------
    selected_name = st.selectbox("Select a Workflow to inspect:", list(filtered_wfs.keys()))
    wf = filtered_wfs[selected_name]

    # Visual DAG
    dot = graphviz.Digraph()
    dot.attr(rankdir='LR', bgcolor='transparent')
    for i, t in enumerate(wf['tasks']):
        node_col = "#ff4b4b" if t['status'] == "FAILED" else "#00c853"
        dot.node(t['name'], f"{t['name']}\n({t['status']})", color=node_col, fontcolor="white", style="filled")
        if i < len(wf['tasks']) - 1:
            dot.edge(t['name'], wf['tasks'][i+1]['name'], color="white")
    
    st.graphviz_chart(dot)

    # Breakdown Table
    for task in wf['tasks']:
        with st.expander(f"Task: {task['name']} - {task['status']}"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write(f"**Source:** {task['src']} | **Target:** {task['tgt']}")
                if task['status'] == "FAILED":
                    team, cat = get_routing(task['log'])
                    st.error(f"Owner: {team}")
            with c2:
                st.code(task['log'])
                if task['status'] == "FAILED" and client:
                    if st.button("AI Analyze", key=task['name']):
                        resp = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": f"Fix this Infa error: {task['log']}"}]
                        )
                        st.info(resp.choices[0].message.content)
