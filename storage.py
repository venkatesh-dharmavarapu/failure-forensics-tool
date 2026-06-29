import os
import sqlite3
import json
from models import Trace

DB_NAME = "pipeline_telemetry.db"
TRACES_DIR = "traces"

def init_db():
    """Initializes the SQLite database schema if it doesn't exist."""
    os.makedirs(TRACES_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Store high-level metadata for query filtering and aggregation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS traces (
            trace_id TEXT PRIMARY KEY,
            timestamp REAL,
            final_status TEXT,
            root_cause_step TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_trace(trace: Trace):
    """Saves trace metadata to SQLite and stores the full raw JSON trace payload to disk."""
    init_db()
    
    # 1. Save full JSON trace representation to a local directory
    file_path = os.path.join(TRACES_DIR, f"{trace.trace_id}.json")
    with open(file_path, "w") as f:
        f.write(trace.model_dump_json(indent=2))
        
    # 2. Index core values into the SQLite database for fast lookups later
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO traces (trace_id, timestamp, final_status, root_cause_step)
        VALUES (?, ?, ?, ?)
    ''', (trace.trace_id, trace.timestamp, trace.final_status, trace.root_cause_step))
    
    conn.commit()
    conn.close()
    print(f"[Storage] Trace metadata indexed to SQLite database. Full payload written to {file_path}")