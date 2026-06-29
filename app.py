import streamlit as st
import sqlite3
import json
import os
from models import Trace
import analyzer

DB_NAME = "pipeline_telemetry.db"
TRACES_DIR = "traces"

st.set_page_config(page_title="AI Failure Forensics Tool", layout="wide")

st.title("🕵️‍♂️ Failure Forensics Tool for AI Pipelines")
st.caption("Production observability & automated root-cause diagnostics")

# --- DATABASE FETCH HELPERS ---
def get_all_traces():
    if not os.path.exists(DB_NAME):
        return []
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT trace_id, timestamp, final_status, root_cause_step FROM traces ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def load_trace_json(trace_id):
    file_path = os.path.join(TRACES_DIR, f"{trace_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return None

# --- SIDEBAR: TRACE LIST ---
traces = get_all_traces()

st.sidebar.header("Execution Traces")
if not traces:
    st.sidebar.info("No traces found. Run main.py to generate pipeline logs.")
    selected_trace_id = None
else:
    trace_options = [f"{row[0]} ({row[2]})" for row in traces]
    selected_option = st.sidebar.selectbox("Select a Trace ID", trace_options)
    selected_trace_id = selected_option.split(" ")[0]

# --- MAIN WORKSPACE ---
if selected_trace_id:
    trace_data = load_trace_json(selected_trace_id)
    
    if trace_data:
        # Header Status Blocks
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Trace ID", trace_data["trace_id"])
        with col2:
            status = trace_data["final_status"]
            status_color = "🔴" if status == "degraded" else "🟢"
            st.metric("Pipeline Status", f"{status_color} {status.upper()}")
        with col3:
            st.metric("Pre-indexed Root Cause", str(trace_data.get("root_cause_step") or "None"))
            
        st.write("---")
        
        # Action Block: Run Forensics Engine
        st.subheader("⚡ Automated Forensic Investigation")
        if st.button("Run Backward Trace Analysis (LLM-as-a-Judge)"):
            with st.spinner("Analyzing intermediate step spans backward..."):
                # Reconstruct trace model instance
                trace_obj = Trace(**trace_data)
                diagnosis = analyzer.analyze_trace_failures(trace_obj)
                
                # Show results in a nice callout box
                if diagnosis["root_cause_step"] != "None (Pipeline Healthy)":
                    st.error(f"🚨 **Root Cause Isolated: {diagnosis['root_cause_step']}**")
                    st.warning(f"**Failure Category:** {diagnosis['failure_category']}")
                    st.info(f"**Judge Verdict Explanation:** \"{diagnosis['explanation']}\"")
                else:
                    st.success("🎉 All pipeline steps verified clean by LLM-as-a-judge.")
                    
                # Expandable Evidence Audit Logs
                with st.expander("View Full Evidence Chain Details"):
                    st.json(diagnosis["evidence_chain"])
                    
        st.write("---")
        
        # Visual Node Timeline Tree Explorer
        st.subheader("📊 Pipeline Span Timeline Explorer")
        
        for span in trace_data.get("spans", []):
            span_status = span.get("status", "success")
            
            # Choose color boundaries based on individual span node health
            if span_status == "success":
                accent = "green"
                icon = "✅"
            elif span_status == "degraded":
                accent = "orange"
                icon = "⚠️"
            else:
                accent = "red"
                icon = "❌"
                
            with st.container():
                st.markdown(
                    f"<div style='border-left: 5px solid {accent}; padding-left: 15px; margin-bottom: 15px;'>", 
                    unsafe_allow_html=True
                )
                
                # Title Bar for individual Node container
                conf = f"| Confidence: {span['confidence_score']}/5" if span.get("confidence_score") else ""
                st.markdown(f"#### {icon} Step: {span['step_name']} <span style='font-size:14px; color:gray;'>({span['latency_ms']} ms {conf})</span>", unsafe_allow_html=True)
                
                # Multi-column Diff layouts
                in_col, out_col = st.columns(2)
                with in_col:
                    st.caption("📥 Data Input Payload")
                    st.json(span["input_data"])
                with out_col:
                    st.caption("📤 Data Output Produced")
                    st.json(span["output_data"])
                    
                st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("💡 Run `python main.py` in your terminal to process documents and generate initial telemetry database rows.")