import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone
from collector.core.models import Job, CollectorRun, Source, iso_now

class Exporter:
    def __init__(self, output_dir: str | Path = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_jobs(self, jobs: list[Job], filename: str = "jobs.json") -> Path:
        """Exports public job data (scrubbed of internal PII or private feedback)."""
        target_path = self.output_dir / filename
        public_jobs = []
        for j in jobs:
            if j.status == "CLOSED":
                continue
            d = j.to_dict()
            # Ensure display freshness label
            display_freshness = "First seen "
            if j.freshness_confidence in ("HIGH", "MEDIUM") and j.posted_at:
                display_freshness = "Published "
            d["display_freshness_type"] = display_freshness
            public_jobs.append(d)

        self._write_json(target_path, public_jobs)
        return target_path

    def export_metadata(self, run: CollectorRun, filename: str = "metadata.json") -> Path:
        """Exports run metadata and summary statistics."""
        target_path = self.output_dir / filename
        metadata = {
            "last_updated_at": iso_now(),
            "last_run": run.to_dict(),
        }
        self._write_json(target_path, metadata)
        return target_path

    def export_source_health(self, sources: list[Source], filename: str = "source-health.json") -> Path:
        """Exports public health status of monitored sources."""
        target_path = self.output_dir / filename
        health_summary = [
            {
                "source_id": s.source_id,
                "company_name": s.company_name,
                "ats_platform": s.ats_platform,
                "tier": s.tier,
                "source_value_score": s.source_value_score,
                "health_status": s.health_status,
                "last_success_at": s.last_success_at.isoformat() if s.last_success_at else None,
            }
            for s in sources
        ]
        self._write_json(target_path, health_summary)
        return target_path

    def _write_json(self, filepath: Path, content: Any) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)
