from datetime import datetime, timezone
from collector.sources.dataset.jobhive import JobhiveReader

def test_manifest_partition_selection():
    manifest_data = {
        "generated_at": "2026-09-30T12:00:00Z",
        "partitions": [
            {"ats": "greenhouse", "path": "greenhouse/jobs.parquet", "rows": 400000},
            {"ats": "lever", "path": "lever/jobs.parquet", "rows": 150000},
            {"ats": "bamboohr", "path": "bamboohr/jobs.parquet", "rows": 90000}, # Not in default targets
        ]
    }
    
    reader = JobhiveReader(target_ats={"greenhouse", "lever"})
    gen_at, selected = reader.parse_manifest(manifest_data)
    
    assert gen_at is not None
    assert len(selected) == 2
    ats_names = {p["ats"] for p in selected}
    assert ats_names == {"greenhouse", "lever"}

def test_filter_job_record_relevance_and_provenance():
    reader = JobhiveReader()
    now = datetime.now(timezone.utc)
    
    # 1. Matching Java job in Bengaluru
    row_match = {
        "id": "jh-101",
        "title": "Senior Java Developer - Spring Boot",
        "company": "TechIndia",
        "location": "Bengaluru, India",
        "source_url": "https://example.com/jh-101"
    }
    job = reader.filter_job_record(row_match, snapshot_at=now)
    assert job is not None
    assert job.source == "ats_scrapers_jobhive"
    assert job.source_type == "ATS_DATASET_SNAPSHOT"
    assert job.freshness_confidence == "SNAPSHOT_ONLY"
    assert job.dataset_snapshot_at == now
    assert job.company == "TechIndia"
    
    # 2. Non-matching title (Python dev)
    row_no_match = {
        "id": "jh-102",
        "title": "Python Django Engineer",
        "company": "TechIndia",
        "location": "Bengaluru, India"
    }
    job_no = reader.filter_job_record(row_no_match, snapshot_at=now)
    assert job_no is None

    # 3. Matching title but non-matching location (London, UK)
    row_wrong_loc = {
        "id": "jh-103",
        "title": "Java Spring Developer",
        "company": "GlobalCorp",
        "location": "London, UK"
    }
    job_loc = reader.filter_job_record(row_wrong_loc, snapshot_at=now)
    assert job_loc is None
