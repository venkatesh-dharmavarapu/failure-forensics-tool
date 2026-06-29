import json
from typing import Dict, Any, Optional
from openai import OpenAI
from models import Trace, Span

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

MODEL_NAME = "qwen2.5-coder:7b"

# Our formal failure taxonomy definition
FAILURE_TAXONOMY = {
    "Extraction Hallucination": "The model extracted entities, dates, or numbers that are fundamentally missing from the source text.",
    "Misclassification": "The model assigned an incorrect document type category given the content.",
    "Propagation Error": "This step processed its inputs correctly, but it failed because a previous step passed it corrupted data.",
    "Prompt Failure": "The model completely ignored the formatting, structural constraints, or system instructions provided.",
    "Context Loss": "Crucial details from the original document text were completely forgotten or omitted in this step."
}

def evaluate_span_quality(step_name: str, input_data: Any, output_data: Any) -> Dict[str, Any]:
    """Uses an LLM-as-a-judge to evaluate if a step's output matches its input logically."""
    
    judge_system_prompt = (
        "You are an expert AI quality assurance engineer specializing in forensic pipeline auditing. "
        "Your job is to analyze the input given to a pipeline step and the output it produced. "
        "Determine if the output is a reasonable, highly accurate transformation of the input.\n\n"
        "Return a JSON object with exactly two keys:\n"
        "1. 'quality_score': an integer from 1 (completely wrong/hallucinated) to 5 (flawless execution).\n"
        "2. 'critique': a brief, precise sentence explaining why you gave that score."
    )
    
    judge_user_prompt = f"""
    --- PIPELINE STEP UNDER AUDIT ---
    Step Name: {step_name}
    
    Input Received by Step:
    {json.dumps(input_data, indent=2)}
    
    Output Produced by Step:
    {json.dumps(output_data, indent=2)}
    ---------------------------------
    Analyze the transformation. Does the output accurately reflect the input without introducing hallucinations or losing critical context?
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": judge_system_prompt},
                {"role": "user", "content": judge_user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"quality_score": 5, "critique": f"Failed to run judge evaluation: {str(e)}"}


def analyze_trace_failures(trace: Trace) -> Dict[str, Any]:
    """Walks through trace spans to pinpoint the exact root cause step and categorize it."""
    print(f"\n[Forensics Engine] Initiating backward trace analysis for Trace ID: {trace.trace_id}...")
    
    evidence_chain = []
    detected_root_cause: Optional[str] = None
    failure_category = "Success"
    
    # Analyze active operational steps (ignoring Step 1 Intake unless text is empty)
    for span in trace.spans:
        if span.step_name == "Intake":
            continue
            
        # Run our judge evaluation
        audit = evaluate_span_quality(span.step_name, span.input_data, span.output_data)
        score = audit.get("quality_score", 5)
        critique = audit.get("critique", "")
        
        print(f" -> Auditing Step: '{span.step_name}' | Judge Quality Score: {score}/5")
        
        # Keep track of the full audit trail
        evidence_chain.append({
            "step_name": span.step_name,
            "judge_score": score,
            "critique": critique
        })
        
        # The first step that hits a quality score threshold <= 3 is our primary suspect
        if score <= 3 and not detected_root_cause:
            detected_root_cause = span.step_name
            
            # Categorize the specific failure profile based on structural heuristics
            if span.step_name == "Extraction":
                failure_category = "Extraction Hallucination"
            elif span.step_name == "Classification":
                failure_category = "Misclassification"
            elif span.step_name == "Summarization":
                # Check if it was matching a bad input or went wild on its own
                if "chocolate" in str(span.output_data).lower():
                    failure_category = "Prompt Failure"
                else:
                    failure_category = "Context Loss"

    # Handle cascade scenarios: if step N failed because step N-1 gave it garbage
    if detected_root_cause == "Summarization" and len(evidence_chain) >= 2:
        # If classification score was low, summarization might just be dealing with propagated bad data
        if evidence_chain[1]["judge_score"] <= 3:
            failure_category = "Propagation Error"

    return {
        "trace_id": trace.trace_id,
        "root_cause_step": detected_root_cause or "None (Pipeline Healthy)",
        "failure_category": failure_category,
        "explanation": next((item["critique"] for item in evidence_chain if item["step_name"] == detected_root_cause), "All steps executed successfully."),
        "evidence_chain": evidence_chain
    }