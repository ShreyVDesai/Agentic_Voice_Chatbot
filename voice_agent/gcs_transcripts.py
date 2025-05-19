import os
import json
from datetime import datetime
from google.cloud import storage

# Read env vars
PROJECT_ID = os.getenv("GCP_PROJECT")
BUCKET_NAME = os.getenv("TRANSCRIPTS_BUCKET")

# Initialize client once
_storage_client = storage.Client(project=PROJECT_ID)
_bucket = _storage_client.bucket(BUCKET_NAME)

def append_transcript_entry(call_sid: str, user_text: str, agent_text: str):
    """
    Append a single JSON line to the transcripts blob for this call.
    Each line has: timestamp, call_sid, user_text, agent_text.
    """
    blob_name = f"transcripts/{call_sid}.jsonl"
    blob = _bucket.blob(blob_name)

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "call_sid": call_sid,
        "user_text": user_text,
        "agent_text": agent_text,
    }
    line = json.dumps(entry, ensure_ascii=False)

    # Download existing contents (if any), append the new line, and re‑upload.
    # Note: for very high volume you’d want a more streaming‑friendly approach.
    existing = ""
    if blob.exists():
        existing = blob.download_as_text()
    updated = existing + line + "\n"
    blob.upload_from_string(updated, content_type="application/json")
