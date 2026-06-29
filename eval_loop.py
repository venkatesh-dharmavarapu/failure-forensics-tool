import os
import json
from typing import List, Dict, Any
from models import Trace

EVAL_DATASET_FILE = "eval_dataset.json"

def log_failure_to_eval_suite(trace: Trace, human_corrected_output: str, confirmed_category: str):
    """
    Transforms a confirmed failure trace into a permanent test case 
    inside our regression evaluation dataset suite.
    """
    # 1. Extract the original input text from the Intake step
    intake_span = next((s for s in trace.spans if s.step_name == "Intake"), None)
    if not intake_span:
        return
        
    raw_input_text = intake_span.input_data.get("raw_text", "")
    
    # 2. Build our structured evaluation test case object
    test_case = {
        "test_case_id": f"eval_{trace.trace_id}",
        "raw_text": raw_input_text,
        "failing_step": trace.root_cause_step or "Summarization",
        "failure_category": confirmed_category,
        "expected_ground_truth": human_corrected_output
    }
    
    # 3. Read existing evaluation cases or create a new array
    dataset: List[Dict[str, Any]] = []
    if os.path.exists(EVAL_DATASET_FILE):
        try:
            with open(EVAL_DATASET_FILE, "r") as f:
                dataset = json.load(f)
        except json.JSONDecodeError:
            dataset = []
            
    # Avoid inserting duplicate test profiles for the same trace sequence
    if not any(item["test_case_id"] == test_case["test_case_id"] for item in dataset):
        dataset.append(test_case)
        with open(EVAL_DATASET_FILE, "w") as f:
            json.dump(dataset, f, indent=2)
        print(f"[Eval Loop] Successfully appended failure profile to {EVAL_DATASET_FILE}")


def run_regression_suite() -> Dict[str, Any]:
    """
    Loops through our collected evaluation test suite, processes them 
    through the active pipeline, and determines if old failures are now fixed.
    """
    import pipeline  # Lazy import to avoid cyclic dependency hiccups
    from models import IntakeInput
    
    if not os.path.exists(EVAL_DATASET_FILE):
        return {"status": "error", "message": "No evaluation items present yet."}
        
    with open(EVAL_DATASET_FILE, "r") as f:
        test_cases = json.load(f)
        
    passed_cases = 0
    total_cases = len(test_cases)
    results_log = []
    
    print(f"\n[Regression Runner] Executing testing verification across {total_cases} historical failure items...")
    
    for case in test_cases:
        # Run the document back through the active engine pipeline
        try:
            intake = pipeline.step_1_intake(IntakeInput(raw_text=case["raw_text"]))
            extract = pipeline.step_2_extraction(intake)
            classify = pipeline.step_3_classification(intake)
            summary = pipeline.step_4_summarization(intake, doc_type=classify.document_type)
            
            # Flush the trace generated during testing so it doesn't leak
            pipeline.flush_trace()
            
            # Simple evaluation heuristic checking: If confidence recovers, mark it fixed!
            is_fixed = summary.confidence_score >= 4
            if is_fixed:
                passed_cases += 1
                
            results_log.append({
                "test_case_id": case["test_case_id"],
                "failure_category": case["failure_category"],
                "is_resolved": is_fixed,
                "current_summary": summary.summary
            })
        except Exception as e:
            results_log.append({
                "test_case_id": case["test_case_id"],
                "is_resolved": False,
                "error": str(e)
            })
            
    return {
        "total_cases": total_cases,
        "resolved_cases": passed_cases,
        "accuracy_rate": round((passed_cases / total_cases) * 100, 2) if total_cases > 0 else 0.0,
        "results": results_log
    }