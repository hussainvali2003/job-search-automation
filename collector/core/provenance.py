import hashlib
from typing import Optional
from collector.core.models import Job

def generate_job_id(source_name: str, source_job_id: str) -> str:
    """Generates a stable deterministic identity key for a job posting."""
    raw = f"{source_name}:{source_job_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

def build_canonical_url(raw_url: str) -> str:
    """Strips tracking query parameters from job URLs."""
    if not raw_url:
        return ""
    # Strip common query params like ?gh_jid=... or utm_*
    base = raw_url.split("?")[0]
    return base.strip()
