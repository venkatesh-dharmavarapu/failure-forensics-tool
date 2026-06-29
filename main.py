import pipeline
import storage
from models import IntakeInput

def run_forensics_hubs():
    # Initialize the local database structural framework
    storage.init_db()
    
    # --- SUCCESS SCENARIO ---
    doc_success = (
        "ACME Corp Service Agreement. Date: June 15, 2026. "
        "This contract outlines that client John Doe will pay $5,000 to ACME Corp for software development services."
    )
    print("\nExecuting Scenario 1: Clean Execution...")
    intake_1 = pipeline.step_1_intake(IntakeInput(raw_text=doc_success))
    pipeline.step_2_extraction(intake_1)
    class_1 = pipeline.step_3_classification(intake_1)
    pipeline.step_4_summarization(intake_1, doc_type=class_1.document_type)
    
    trace_1 = pipeline.flush_trace()
    storage.save_trace(trace_1)

    # --- FAILURE / DEGRADED SCENARIO ---
    doc_failure = "URGENT Internal Memo. The corporate strategy document needs review next week."
    print("\nExecuting Scenario 2: Failure Injection (Step 4 Summarization Intercept)...")
    intake_2 = pipeline.step_1_intake(IntakeInput(raw_text=doc_failure))
    pipeline.step_2_extraction(intake_2)
    class_2 = pipeline.step_3_classification(intake_2)
    # Injecting failure mode toggle flag to Step 4
    pipeline.step_4_summarization(intake_2, doc_type=class_2.document_type, simulate_failure=True)
    
    trace_2 = pipeline.flush_trace()
    storage.save_trace(trace_2)

if __name__ == "__main__":
    run_forensics_hubs()