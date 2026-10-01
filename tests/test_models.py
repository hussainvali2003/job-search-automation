from datetime import datetime, timezone
import pytest
from collector.core.models import Job, Source, CollectorRun, UserAction

def test_job_model_provenance_and_serialization():
    now = datetime.now(timezone.utc)
    job = Job(
        source="greenhouse",
        source_type="ATS_DIRECT",
        source_job_id="gh-12345",
        source_url="https://boards.greenhouse.io/infosys/jobs/12345",
        company="Infosys",
        title="Java Backend Engineer",
        posted_at=now,
        freshness_confidence="HIGH"
    )
    
    assert job.source_type == "ATS_DIRECT"
    assert job.freshness_confidence == "HIGH"
    assert job.company_normalized == "infosys"
    assert job.title_normalized == "java backend engineer"
    
    d = job.to_dict()
    assert d["source"] == "greenhouse"
    assert d["company"] == "Infosys"
    assert d["freshness_confidence"] == "HIGH"
    assert d["posted_at"] is not None
    
    restored = Job.from_dict(d)
    assert restored.id == job.id
    assert restored.company == "Infosys"
    assert restored.source_type == "ATS_DIRECT"
    assert restored.freshness_confidence == "HIGH"

def test_source_model_score_and_tier_promotion():
    source = Source(
        source_id="lever_razorpay",
        company_name="Razorpay",
        ats_platform="lever",
        board_token="razorpay",
        base_url="https://api.lever.co/v0/postings/razorpay",
        tier="P2",
        source_value_score=50.0,
        relevant_jobs_30d=8,
        fresh_jobs_30d=5,
        total_jobs_fetched_30d=20,
        total_requests_30d=50,
        successful_requests_30d=50,
        failed_requests_30d=0,
        consecutive_failures=0
    )
    
    score = source.calculate_score()
    assert score >= 75.0
    
    new_tier = source.evaluate_tier_promotion()
    assert new_tier == "P0"
    assert source.poll_interval_minutes == 15

def test_source_demotion_on_failures():
    source = Source(
        source_id="broken_source",
        company_name="BrokenCorp",
        ats_platform="greenhouse",
        board_token="broken",
        base_url="https://api.greenhouse.io/v1/broken",
        tier="P0",
        consecutive_failures=10
    )
    
    new_tier = source.evaluate_tier_promotion()
    assert new_tier == "P3"
    assert source.health_status == "SUSPECTED_BROKEN"

def test_collector_run_lifecycle():
    run = CollectorRun(tier_run="P0")
    assert run.status == "RUNNING"
    assert run.finished_at is None
    
    run.jobs_fetched = 10
    run.jobs_new = 8
    run.finalize("COMPLETED")
    
    assert run.status == "COMPLETED"
    assert run.finished_at is not None
    assert run.duration_seconds >= 0.0

def test_user_action_model():
    action = UserAction(job_id="job-99", action_type="SAVED", notes="Interested in this role")
    d = action.to_dict()
    assert d["action_type"] == "SAVED"
    assert d["notes"] == "Interested in this role"
    
    restored = UserAction.from_dict(d)
    assert restored.job_id == "job-99"
    assert restored.action_type == "SAVED"
