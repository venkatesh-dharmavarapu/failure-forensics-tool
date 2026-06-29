# 🕵️‍♂️ Failure Forensics Tool for AI Pipelines

An enterprise-grade, local observability and telemetry tracing layer designed to debug multi-step LLM orchestration pipelines. This tool maps execution variables, captures intermediate system data states down to the millisecond, and employs an automated **LLM-as-a-judge** routine to isolate and resolve black-box pipeline failures.

---

## 🏗️ System Architecture & Data Flow

Below is the design lifecycle profile mapping how raw inputs transition through isolated structural evaluation boundaries into the database registry and human feedback validation loops:

[ Raw Document Input ]
│
▼
┌────────────────────────────────────────────────────────┐
│ ⚙️ 4-Step Processing Pipeline                           │
│   1. Intake ──► 2. Extraction ──► 3. Classification ──►│ 4. Summarization
└────────────────────────────────────────────────────────┘
│
├─► [ 🛰️ TraceContext Manager ] ──► Captures Latency, Spans, & JSON payloads
│
▼
┌────────────────────────────────────────────────────────┐
│ 💾 Telemetry Storage (SQLite Index + Raw JSON Files)   │
└────────────────────────────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────┐
│ 🖥️ Streamlit Web Dashboard App                        │
└────────────────────────────────────────────────────────┘
│
├─► [ 🧠 LLM-as-a-Judge Forensics Engine ] ──► Pinpoints Root-Cause
│
└─► [ 🔄 Feedback-to-Eval Loop ] ──► Generates Regression Test Suites

---

## 🛠️ Tech Stack & Architecture Design Choices

* **Runtime Environment:** Python 3.11+
* **Orchestration Core:** Deep custom chaining structured around strict **Pydantic v2** data constraints (avoids heavy library abstractions like LangChain to maximize telemetry precision).
* **Local Inference Engine:** **Ollama (`qwen2.5-coder:7b`)** serving structured JSON schema patterns locally to achieve zero token operation costs.
* **Telemetry Specification:** Custom context-bound wrapper tracking systems matching production **OpenTelemetry** span conventions.
* **Storage Layer:** Atomic transactional indexing via SQLite complemented by human-inspectable local JSON file blocks.
* **User Interface:** Streamlit interactive browser network tracking node panels.

---

## 🚀 Getting Started (Local Quickstart)

### 1. Clone & Initialize Environment
```powershell
git clone [https://github.com/YOUR_GITHUB_USERNAME/failure-forensics-tool.git](https://github.com/YOUR_GITHUB_USERNAME/failure-forensics-tool.git)
cd failure-forensics-tool

# Initialize and activate the virtual wrapper
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

### 2. Verify Local Model Availability
Ensure your local Ollama background engine service is running with your target compiler dependencies downloaded:

PowerShell : ollama run qwen2.5-coder:7b

### 3. Generate Telemetry Logs & Launch Dashboard
Execute the pipeline simulation sequence to seed your local database framework:

PowerShell : python main.py

### 4. Launch the interactive web portal to analyze your diagnostic reports:

PowerShell : streamlit run app.py