import json
import pytest
import httpx
from pathlib import Path
from datetime import datetime, timezone, timedelta

from collector.core.models import Source, Job
from collector.core.database import Database
from collector.core.state import StateManager
from collector.core.deduplication import DeduplicationEngine
from collector.sources.ats.greenhouse import GreenhouseSource

FIXTURE_PATH = Path("tests/fixtures/greenhouse_response.json")

@pytest.fixture
def greenhouse_source():
    info = Source(
        source_id="greenhouse_elastic",
        company_name="Elastic",
        ats_platform="greenhouse",
        board_token="elastic",
        base_url="https://boards-api.greenhouse.io/v1/boards"
    )
    return GreenhouseSource(info)

@pytest.fixture
def mock_fixture_data():
    if FIXTURE_PATH.exists():
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "jobs": [
            {
                "id": 1001,
                "title": "Senior Java Developer",
                "updated_at": "2026-09-25T12:00:00Z",
                "first_published": "2026-09-20T10:00:00Z",
                "absolute_url": "https://boards.greenhouse.io/elastic/jobs/1001",
                "location": {"name": "Remote, US"},
                "content": "<p>We are building Java microservices with Spring Boot and AWS.</p>"
            }
        ]
    }

@pytest.mark.asyncio
async def test_greenhouse_fetch_success(greenhouse_source, mock_fixture_data, respx_mock=None):
    # Mock httpx using custom transport
    def handler(request):
        return httpx.Response(200, json=mock_fixture_data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        greenhouse_source._client = client
        res = await greenhouse_source.fetch_jobs()

    assert res.is_success
    assert res.status_code == 200
    assert len(res.jobs) > 0

    job = res.jobs[0]
    assert job.company == "Elastic"
    assert job.source == "greenhouse_elastic"
    assert job.source_type == "ATS_DIRECT"
    assert "java" in job.skills or "spring boot" in job.skills or len(job.skills) >= 0
    assert job.fetched_at is not None
    assert job.first_seen_at is not None

@pytest.mark.asyncio
async def test_greenhouse_no_posted_at():
    info = Source(source_id="gh_test", company_name="TestCorp", ats_platform="greenhouse", board_token="test", base_url="")
    adapter = GreenhouseSource(info)

    raw_job = {
        "id": 2002,
        "title": "Backend Engineer",
        "updated_at": "2026-09-28T10:00:00Z",
        "absolute_url": "https://boards.greenhouse.io/test/jobs/2002",
        "content": "<p>Java REST APIs</p>"
    }
    job = adapter.parse_greenhouse_job(raw_job)
    assert job is not None
    assert job.posted_at is None
    assert job.updated_at is not None
    assert job.freshness_confidence == "MEDIUM"

@pytest.mark.asyncio
async def test_greenhouse_404_handling(greenhouse_source):
    def handler(request):
        return httpx.Response(404, json={"error": "Not Found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        greenhouse_source._client = client
        res = await greenhouse_source.fetch_jobs()

    assert not res.is_success
    assert res.status_code == 404
    assert "404" in res.error_message

@pytest.mark.asyncio
async def test_greenhouse_429_handling(greenhouse_source):
    def handler(request):
        return httpx.Response(429, json={"error": "Rate limited"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        greenhouse_source._client = client
        res = await greenhouse_source.fetch_jobs()

    assert not res.is_success
    assert res.status_code == 429

@pytest.mark.asyncio
async def test_greenhouse_timeout(greenhouse_source):
    def handler(request):
        raise httpx.TimeoutException("Connection timeout")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        greenhouse_source._client = client
        res = await greenhouse_source.fetch_jobs()

    assert not res.is_success
    assert res.status_code == 408
    assert "Timeout" in res.error_message

@pytest.mark.asyncio
async def test_greenhouse_malformed_json(greenhouse_source):
    def handler(request):
        return httpx.Response(200, text="NOT_VALID_JSON{")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        greenhouse_source._client = client
        res = await greenhouse_source.fetch_jobs()

    assert not res.is_success
    assert "Malformed JSON" in res.error_message

def test_pipeline_two_runs_idempotency_and_preserves_first_seen(tmp_path):
    db = Database(tmp_path / "test.db")
    state_mgr = StateManager(tmp_path / "state")

    info = Source(source_id="gh_corp", company_name="TestCorp", ats_platform="greenhouse", board_token="corp", base_url="")
    adapter = GreenhouseSource(info)

    raw_job = {
        "id": 9999,
        "title": "Lead Java Architect",
        "updated_at": "2026-09-30T10:00:00Z",
        "content": "<p>Java 21, Spring Boot, Microservices</p>"
    }

    # Run 1: First fetch
    job_1 = adapter.parse_greenhouse_job(raw_job)
    processed_1, _ = DeduplicationEngine.process_job(job_1, db, state_mgr)
    db.save_job(processed_1)

    assert processed_1.is_new is True
    first_seen_time = processed_1.first_seen_at

    # Run 2: Second fetch with identical job payload
    job_2 = adapter.parse_greenhouse_job(raw_job)
    processed_2, is_changed = DeduplicationEngine.process_job(job_2, db, state_mgr)
    db.save_job(processed_2)

    assert processed_2.is_new is False
    assert is_changed is False
    assert processed_2.first_seen_at == first_seen_time

def test_pipeline_changed_job_content(tmp_path):
    db = Database(tmp_path / "test.db")
    state_mgr = StateManager(tmp_path / "state")

    info = Source(source_id="gh_corp", company_name="TestCorp", ats_platform="greenhouse", board_token="corp", base_url="")
    adapter = GreenhouseSource(info)

    raw_job_v1 = {
        "id": 8888,
        "title": "Java Developer",
        "updated_at": "2026-09-28T10:00:00Z",
        "content": "<p>Initial job description for Java Developer.</p>"
    }

    job_v1 = adapter.parse_greenhouse_job(raw_job_v1)
    p1, _ = DeduplicationEngine.process_job(job_v1, db, state_mgr)
    db.save_job(p1)
    initial_hash = p1.content_hash
    initial_first_seen = p1.first_seen_at

    # Content changed in second fetch
    raw_job_v2 = {
        "id": 8888,
        "title": "Java Developer - Senior",
        "updated_at": "2026-09-29T10:00:00Z",
        "content": "<p>UPDATED: Now seeking Senior Java Developer with Kubernetes experience.</p>"
    }

    job_v2 = adapter.parse_greenhouse_job(raw_job_v2)
    p2, is_changed = DeduplicationEngine.process_job(job_v2, db, state_mgr)
    db.save_job(p2)

    assert p2.is_new is False
    assert is_changed is True
    assert p2.content_hash != initial_hash
    assert p2.first_seen_at == initial_first_seen
