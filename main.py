import pipeline
import storage
import analyzer
from models import IntakeInput

def run_forensics_hubs():
    # Initialize local directories and database
    storage.init_db()
    
    # --- SCENARIO: RUNNING DEGRADED PIPELINE ---
    doc_failure = "URGENT Internal Memo. The corporate strategy document needs review next week."
    print("\n================ EXECUTING PIPELINE (WITH FAILURE MODE) ================")
    
    intake = pipeline.step_1_intake(IntakeInput(raw_text=doc_failure))
    pipeline.step_2_extraction(intake)
    class_out = pipeline.step_3_classification(intake)
    
    # Purposefully inject the failure flag into step 4
    pipeline.step_4_summarization(intake, doc_type=class_out.document_type, simulate_failure=True)
    
    # Pull the trace and index it
    trace = pipeline.flush_trace()
    storage.save_trace(trace)

    # --- FORENSIC ANALYSIS BLOCK ---
    print("\n================ AUTOMATED ROOT-CAUSE FORENSICS ================")
    diagnosis = analyzer.analyze_trace_failures(trace)
    
    print("\n[DIAGNOSTIC REPORT GENERATED]:")
    print(f" • Identified Root Cause Step : {diagnosis['root_cause_step']}")
    print(f" • Forensic Failure Category  : {diagnosis['failure_category']}")
    print(f" • Judge Verdict Explanation : \"{diagnosis['explanation']}\"")

if __name__ == "__main__":
    run_forensics_hubs()