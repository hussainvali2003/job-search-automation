from datetime import datetime, timezone, timedelta
import pytest
from collector.core.database import Database
from collector.core.models import Job, Source, CollectorRun

def test_database_job_crud_and_first_seen_preservation():
    db = Database(":memory:")
    
    t1 = datetime.now(timezone.utc) - timedelta(days=2)
    job = Job(
        id="job-uuid-1",
        source="greenhouse",
        source_type="ATS_DIRECT",
        source_job_id="101",
        company="TestCorp",
        title="Java Engineer",
        first_seen_at=t1,
        last_seen_at=t1,
        freshness_confidence="HIGH"
    )
    
    db.save_job(job)
    fetched = db.get_job_by_id("job-uuid-1")
    assert fetched is not None
    assert fetched.company == "TestCorp"
    assert fetched.first_seen_at == t1
    
    # Update job last_seen_at
    t2 = datetime.now(timezone.utc)
    job.last_seen_at = t2
    job.title = "Updated Java Engineer"
    db.save_job(job)
    
    updated = db.get_job_by_id("job-uuid-1")
    assert updated is not None
    assert updated.title == "Updated Java Engineer"
    assert updated.first_seen_at == t1  # Must preserve original first_seen_at!

def test_mark_closed_jobs():
    db = Database(":memory:")
    j1 = Job(id="job-1", source="lever", company="CompA", title="Role 1", status="ACTIVE")
    j2 = Job(id="job-2", source="lever", company="CompA", title="Role 2", status="ACTIVE")
    
    db.save_job(j1)
    db.save_job(j2)
    
    # Only j1 is active in current run
    closed_count = db.mark_closed_jobs(active_job_ids={"job-1"}, source_name="lever")
    assert closed_count == 1
    
    res1 = db.get_job_by_id("job-1")
    res2 = db.get_job_by_id("job-2")
    assert res1.status == "ACTIVE"
    assert res2.status == "CLOSED"

def test_source_and_run_persistence():
    db = Database(":memory:")
    source = Source(source_id="src-1", company_name="CompA", ats_platform="greenhouse", board_token="compa", base_url="http://example.com")
    run = CollectorRun(run_id="run-1", tier_run="P0", jobs_fetched=5)
    
    db.save_source(source)
    db.save_run(run)
    
    cur = db.conn.execute("SELECT * FROM sources WHERE source_id = ?", ("src-1",))
    assert cur.fetchone() is not None
    
    cur_run = db.conn.execute("SELECT * FROM runs WHERE run_id = ?", ("run-1",))
    row = cur_run.fetchone()
    assert row["jobs_fetched"] == 5
