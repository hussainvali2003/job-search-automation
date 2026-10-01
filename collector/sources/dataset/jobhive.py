from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Optional
from collector.core.models import Job, parse_iso
from collector.core.logger import logger

DEFAULT_TARGET_ATS = {"greenhouse", "lever", "ashby", "workable", "smartrecruiters"}
DEFAULT_KEYWORDS = {"java", "spring", "backend", "microservices"}
DEFAULT_LOCATIONS = {"india", "remote", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "delhi", "noida", "gurgaon", "ahmedabad"}

class JobhiveReader:
    def __init__(self, target_ats: Optional[set[str]] = None, target_keywords: Optional[set[str]] = None):
        self.target_ats = target_ats or DEFAULT_TARGET_ATS
        self.target_keywords = target_keywords or DEFAULT_KEYWORDS
        self.target_locations = DEFAULT_LOCATIONS

    def parse_manifest(self, manifest_data: dict[str, Any]) -> tuple[Optional[datetime], list[dict[str, Any]]]:
        """Parses manifest dictionary and returns (generated_at, selected_partitions)."""
        gen_at_str = manifest_data.get("generated_at")
        generated_at = parse_iso(gen_at_str) or datetime.now(timezone.utc)
        
        all_partitions = manifest_data.get("partitions", [])
        selected = []
        for p in all_partitions:
            ats_name = p.get("ats", "").lower()
            if ats_name in self.target_ats:
                selected.append(p)
                
        return generated_at, selected

    def filter_job_record(self, raw_row: dict[str, Any], snapshot_at: datetime) -> Optional[Job]:
        """Filters a single raw dataset record by keyword and location relevance."""
        title = str(raw_row.get("title", "")).strip()
        location = str(raw_row.get("location", "")).strip()
        company = str(raw_row.get("company", "")).strip()
        
        title_lower = title.lower()
        loc_lower = location.lower()
        
        # Keyword check
        if not any(kw in title_lower for kw in self.target_keywords):
            return None

        # Location check
        if self.target_locations and not any(loc in loc_lower for loc in self.target_locations):
            return None

        # Construct Job model with explicit SNAPSHOT_ONLY provenance
        job_id = str(raw_row.get("id") or raw_row.get("source_job_id") or f"jh-{hash(title+company)}")
        return Job(
            source="ats_scrapers_jobhive",
            source_type="ATS_DATASET_SNAPSHOT",
            source_job_id=job_id,
            source_url=str(raw_row.get("source_url") or raw_row.get("url") or ""),
            company=company,
            title=title,
            location=location,
            dataset_snapshot_at=snapshot_at,
            freshness_confidence="SNAPSHOT_ONLY",
            posted_at=parse_iso(raw_row.get("posted_at")) if raw_row.get("posted_at_trusted") else None,
            description_snippet=str(raw_row.get("description", ""))[:500] if raw_row.get("description") else None,
            status="ACTIVE",
        )
