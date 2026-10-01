import json
from datetime import datetime, timezone
from collector.core.exporter import Exporter
from collector.core.models import Job, Source, CollectorRun

def test_exporter_public_outputs(tmp_path):
    exporter = Exporter(output_dir=tmp_path)
    
    jobs = [
        Job(
            id="j-1",
            source="greenhouse",
            source_type="ATS_DIRECT",
            source_job_id="100",
            company="CompA",
            title="Java Backend Engineer",
            status="ACTIVE",
            posted_at=datetime.now(timezone.utc),
            freshness_confidence="HIGH"
        ),
        Job(
            id="j-2",
            source="lever",
            source_type="ATS_DIRECT",
            source_job_id="101",
            company="CompB",
            title="Software Engineer",
            status="CLOSED"  # Should be excluded from public jobs.json
        )
    ]
    
    run = CollectorRun(run_id="run-test", tier_run="P0", jobs_fetched=1, jobs_new=1)
    sources = [Source(source_id="src-1", company_name="CompA", ats_platform="greenhouse", board_token="compa", base_url="http://example.com")]
    
    # Export
    jobs_path = exporter.export_jobs(jobs)
    meta_path = exporter.export_metadata(run)
    health_path = exporter.export_source_health(sources)
    
    # Verify jobs.json
    with open(jobs_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 1  # Only ACTIVE job included
        assert data[0]["company"] == "CompA"
        assert data[0]["display_freshness_type"] == "Published "

    # Verify metadata.json
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        assert meta["last_run"]["run_id"] == "run-test"

    # Verify source-health.json
    with open(health_path, "r", encoding="utf-8") as f:
        health = json.load(f)
        assert len(health) == 1
        assert health[0]["source_id"] == "src-1"
