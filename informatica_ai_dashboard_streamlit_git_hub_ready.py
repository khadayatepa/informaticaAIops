import streamlit as st
import graphviz

# ------------------------------
# 1. High-Visibility CSS (Dark Mode Optimization)
# ------------------------------
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    /* Metric Card Styling */
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
# 2. Sample Multi-Workflow Data
# ------------------------------
all_workflows = [
    {
        "id": "wf_sales_daily",
        "status": "FAILED",
        "server": "INFA_PROD_01",
        "db": "SALES_DB",
        "tasks": [
            {"name": "s_m_stage_orders", "status": "SUCCESS", "src": "Oracle_ERP", "tgt": "Staging_DB"},
            {"name": "s_m_load_fact", "status": "FAILED", "src": "Staging_DB", "tgt": "Snowflake_DWH"}
        ]
    },
    {
        "id": "wf_customer_sync",
        "status": "SUCCESS",
        "server": "INFA_PROD_02",
        "db": "CRM_DB",
        "tasks": [
            {"name": "s_m_upsert_cust", "status": "SUCCESS", "src": "Salesforce", "tgt": "Oracle_CRM"}
        ]
    }
]

st.title("🚀 Visual Informatica Infrastructure Pipeline")

# Filter
view_filter = st.radio("Filter View:", ["ALL", "FAILED", "SUCCESS"], horizontal=True)
filtered = [w for w in all_workflows if view_filter == "ALL" or w['status'] == view_filter]

# ------------------------------
# 3. Pipeline Generator with Icons
# ------------------------------
for wf in filtered:
    with st.container():
        st.subheader(f"📦 Workflow: {wf['id']}")
        
        # Create Graphviz object
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR', bgcolor='transparent')

        # Define Global Node Styles
        # 'database' shape represents the DB icon
        # 'rectangle' represents the Server/Informatica icon
        
        for task in wf['tasks']:
            # Determine Color based on status
            status_color = "#ff4b4b" if task['status'] == "FAILED" else "#00c853"
            edge_color = "#ff4b4b" if task['status'] == "FAILED" else "#ffffff"

            # 1. Source DB Node (Database Icon)
            dot.node(f"src_{task['name']}", f"🗄️ {task['src']}\n(Source DB)", 
                     shape="database", color="#00d4ff", fontcolor="white", style="filled")

            # 2. Informatica Server Node (Informatica Icon)
            dot.node(f"srv_{task['name']}", f"💻 {wf['server']}\n(Informatica)", 
                     shape="rectangle", color="#757575", fontcolor="white", style="filled")

            # 3. Specific Session Node (The Task)
            dot.node(task['name'], f"⚙️ {task['name']}\n({task['status']})", 
                     shape="component", color=status_color, fontcolor="white", style="filled")

            # 4. Target DB Node (Database Icon)
            target_color = status_color if task['status'] == "FAILED" else "#00c853"
            dot.node(f"tgt_{task['name']}", f"🎯 {task['tgt']}\n(Target DB)", 
                     shape="database", color=target_color, fontcolor="white", style="filled")

            # Connections (Edges)
            dot.edge(f"src_{task['name']}", f"srv_{task['name']}", color="#ffffff")
            dot.edge(f"srv_{task['name']}", task['name'], color="#ffffff")
            dot.edge(task['name'], f"tgt_{task['name']}", color=edge_color, penwidth="2.0")

        st.graphviz_chart(dot)
        st.markdown("---")
