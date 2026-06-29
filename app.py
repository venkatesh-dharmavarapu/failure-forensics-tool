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
        
        # Initialize session state for holding diagnosis values across re-runs
        if "current_diagnosis" not in st.session_state or st.session_state.get("last_trace_id") != selected_trace_id:
            st.session_state.current_diagnosis = None
            st.session_state.last_trace_id = selected_trace_id

        if st.button("Run Backward Trace Analysis (LLM-as-a-Judge)"):
            with st.spinner("Analyzing intermediate step spans backward..."):
                trace_obj = Trace(**trace_data)
                st.session_state.current_diagnosis = analyzer.analyze_trace_failures(trace_obj)
                
        if st.session_state.current_diagnosis:
            diagnosis = st.session_state.current_diagnosis
            
            if diagnosis["root_cause_step"] != "None (Pipeline Healthy)":
                st.error(f"🚨 **Root Cause Isolated: {diagnosis['root_cause_step']}**")
                st.warning(f"**Failure Category:** {diagnosis['failure_category']}")
                st.info(f"**Judge Verdict Explanation:** \"{diagnosis['explanation']}\"")
                
                st.write("---")
                st.markdown("### 📥 Feedback-to-Eval Loop Integration")
                st.caption("Convert this confirmed pipeline breakdown into a structured regression test case item.")
                
                # Human-in-the-loop manual corrections block
                corrected_text = st.text_area(
                    "Provide Human Corrected/Golden Output Standard Summary:",
                    value="Provide what the clean final summary should have realistically been."
                )
                
                if st.button("Confirm Diagnosis & Commit to Eval Dataset"):
                    import eval_loop
                    trace_obj = Trace(**trace_data)
                    trace_obj.root_cause_step = diagnosis["root_cause_step"]
                    
                    eval_loop.log_failure_to_eval_suite(
                        trace=trace_obj,
                        human_corrected_output=corrected_text,
                        confirmed_category=diagnosis["failure_category"]
                    )
                    st.success("🎉 Added to eval_dataset.json! This case will now be evaluated during regression tracking routines.")
            else:
                st.success("🎉 All pipeline steps verified clean by LLM-as-a-judge.")

            # --- SIDEBAR SUB-SECTION: ACCUMULATED EVAL METRICS ---
            st.sidebar.markdown("---")
            st.sidebar.subheader("📈 Regression Test Center")
            if st.sidebar.button("Run Pipeline Regression Test Suite"):
                import eval_loop
                suite_report = eval_loop.run_regression_suite()
                
                if "status" in suite_report and suite_report["status"] == "error":
                    st.sidebar.error(suite_report["message"])
                else:
                    st.sidebar.metric("Suite Accuracy Rate", f"{suite_report['accuracy_rate']}%")
                    st.sidebar.write(f"Resolved: `{suite_report['resolved_cases']}/{suite_report['total_cases']}` items.")