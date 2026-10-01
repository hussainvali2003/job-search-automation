import pytest
from collector.core.models import Job, Source
from collector.core.database import Database
from collector.core.state import StateManager
from collector.core.deduplication import DeduplicationEngine

def test_cross_source_deduplication(tmp_path):
    db = Database(tmp_path / "dedup.db")
    state_mgr = StateManager(tmp_path / "state")

    # Source A (Greenhouse)
    job_a = Job(
        source="greenhouse_corp",
        source_type="ATS_DIRECT",
        source_job_id="gh-101",
        company="TechCorp",
        title="Senior Java Developer",
        location="Bengaluru, India",
        description="Java microservices development using Spring Boot.",
        content_hash="hash12345"
    )
    p_a, _ = DeduplicationEngine.process_job(job_a, db, state_mgr)
    db.save_job(p_a)

    assert p_a.is_new is True

    # Source B (Lever) - Same company, title, location from different ATS platform
    job_b = Job(
        source="lever_corp",
        source_type="ATS_DIRECT",
        source_job_id="lev-999",
        company="TechCorp",
        title="Senior Java Developer",
        location="Bengaluru, India",
        description="Java microservices development using Spring Boot.",
        content_hash="hash12345"
    )
    p_b, _ = DeduplicationEngine.process_job(job_b, db, state_mgr)
    db.save_job(p_b)

    assert p_b.is_new is False
    assert p_b.duplicate_group_id == p_a.duplicate_group_id
    assert p_b.first_seen_at == p_a.first_seen_at

def test_repost_detection(tmp_path):
    db = Database(tmp_path / "repost.db")
    state_mgr = StateManager(tmp_path / "state")

    # Original posting
    job_v1 = Job(
        source="greenhouse_corp",
        source_type="ATS_DIRECT",
        source_job_id="gh-100",
        company="TechCorp",
        title="Java Engineer",
        location="Hyderabad, India",
        description="Spring Boot Java API engineering.",
        content_hash="hash999"
    )
    p1, _ = DeduplicationEngine.process_job(job_v1, db, state_mgr)
    db.save_job(p1)

    # Reappeared posting on same source with new job ID
    job_v2 = Job(
        source="greenhouse_corp",
        source_type="ATS_DIRECT",
        source_job_id="gh-200",  # New ID
        company="TechCorp",
        title="Java Engineer",
        location="Hyderabad, India",
        description="Spring Boot Java API engineering.",
        content_hash="hash999"
    )
    p2, _ = DeduplicationEngine.process_job(job_v2, db, state_mgr)
    db.save_job(p2)

    assert p2.is_new is False
    assert p2.is_repost is True
    assert p2.duplicate_group_id == p1.duplicate_group_id
    assert p2.first_seen_at == p1.first_seen_at
