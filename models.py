import time
from pydantic import BaseModel, Field
from typing import List, Any, Optional

# ==========================================
# PHASE 1: PIPELINE SCHEMAS
# ==========================================

# --- STEP 1: INTAKE ---
class IntakeInput(BaseModel):
    raw_text: str

class IntakeOutput(BaseModel):
    document_id: str
    processed_text: str

# --- STEP 2: EXTRACTION ---
class ExtractedEntities(BaseModel):
    names: List[str] = Field(default_factory=list, description="Names of people or organizations")
    dates: List[str] = Field(default_factory=list, description="Important dates found in the document")
    amounts: List[str] = Field(default_factory=list, description="Monetary amounts or financial values")
    key_terms: List[str] = Field(default_factory=list, description="Key terms or legal concepts")

class ExtractionOutput(BaseModel):
    entities: ExtractedEntities
    confidence_score: int = Field(description="Confidence rating from 1 to 5")

# --- STEP 3: CLASSIFICATION ---
class ClassificationOutput(BaseModel):
    document_type: str = Field(description="Must be one of: contract, invoice, report, correspondence, or unknown")
    confidence_score: int = Field(description="Confidence rating from 1 to 5")

# --- STEP 4: SUMMARIZATION ---
class SummarizationOutput(BaseModel):
    summary: str = Field(description="A concise summary tailored to the document type")
    confidence_score: int = Field(description="Confidence rating from 1 to 5")


# ==========================================
# PHASE 2: TELEMETRY & TRACING SCHEMAS
# ==========================================

class Span(BaseModel):
    span_id: str
    step_name: str
    input_data: Any 
    output_data: Optional[Any] = None 
    confidence_score: Optional[int] = None
    latency_ms: float = 0.0
    error_message: Optional[str] = None
    status: str = "success"  # success, failure, degraded

class Trace(BaseModel):
    trace_id: str
    timestamp: float = Field(default_factory=time.time)
    spans: List[Span] = Field(default_factory=list)
    final_status: str = "success"
    root_cause_step: Optional[str] = None