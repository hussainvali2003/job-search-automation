import json
import pytest
import httpx
from pathlib import Path
from datetime import datetime, timezone

from collector.core.models import Source, Job
from collector.core.database import Database
from collector.core.state import StateManager
from collector.core.deduplication import DeduplicationEngine
from collector.sources.ats.lever import LeverSource

FIXTURE_PATH = Path("tests/fixtures/lever_response.json")

@pytest.fixture
def lever_source():
    info = Source(
        source_id="lever_palantir",
        company_name="Palantir",
        ats_platform="lever",
        board_token="palantir",
        base_url="https://api.lever.co/v0/postings"
    )
    return LeverSource(info)

@pytest.fixture
def mock_fixture_data():
    if FIXTURE_PATH.exists():
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {
            "id": "lev-101",
            "text": "Software Engineer - Java Infrastructure",
            "createdAt": 1727500000000,
            "hostedUrl": "https://jobs.lever.co/palantir/lev-101",
            "categories": {"location": "New York, NY", "commitment": "Full-time"},
            "descriptionPlain": "Building enterprise Java services at scale."
        }
    ]

@pytest.mark.asyncio
async def test_lever_fetch_success(lever_source, mock_fixture_data):
    def handler(request):
        return httpx.Response(200, json=mock_fixture_data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        lever_source._client = client
        res = await lever_source.fetch_jobs()

    assert res.is_success
    assert res.status_code == 200
    assert len(res.jobs) > 0

    job = res.jobs[0]
    assert job.company == "Palantir"
    assert job.source == "lever_palantir"
    assert job.source_type == "ATS_DIRECT"
    assert job.posted_at is not None
    assert job.freshness_confidence == "HIGH"
    assert job.fetched_at is not None

@pytest.mark.asyncio
async def test_lever_404_handling(lever_source):
    def handler(request):
        return httpx.Response(404, json={"error": "Not Found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        lever_source._client = client
        res = await lever_source.fetch_jobs()

    assert not res.is_success
    assert res.status_code == 404

@pytest.mark.asyncio
async def test_lever_429_handling(lever_source):
    def handler(request):
        return httpx.Response(429, json={"error": "Too Many Requests"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        lever_source._client = client
        res = await lever_source.fetch_jobs()

    assert not res.is_success
    assert res.status_code == 429

@pytest.mark.asyncio
async def test_lever_timeout(lever_source):
    def handler(request):
        raise httpx.TimeoutException("Lever API timeout")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        lever_source._client = client
        res = await lever_source.fetch_jobs()

    assert not res.is_success
    assert res.status_code == 408

def test_lever_pipeline_two_runs_idempotency(tmp_path):
    db = Database(tmp_path / "test.db")
    state_mgr = StateManager(tmp_path / "state")

    info = Source(source_id="lever_palantir", company_name="Palantir", ats_platform="lever", board_token="palantir", base_url="")
    adapter = LeverSource(info)

    raw_job = {
        "id": "lev-202",
        "text": "Senior Systems Engineer (Java)",
        "createdAt": 1727500000000,
        "hostedUrl": "https://jobs.lever.co/palantir/lev-202",
        "categories": {"location": "London, UK"},
        "descriptionPlain": "High throughput Java backend systems."
    }

    # Run 1
    job_1 = adapter.parse_lever_job(raw_job)
    p1, _ = DeduplicationEngine.process_job(job_1, db, state_mgr)
    db.save_job(p1)

    assert p1.is_new is True
    t1 = p1.first_seen_at

    # Run 2
    job_2 = adapter.parse_lever_job(raw_job)
    p2, is_changed = DeduplicationEngine.process_job(job_2, db, state_mgr)
    db.save_job(p2)

    assert p2.is_new is False
    assert is_changed is False
    assert p2.first_seen_at == t1
