import json
import pytest
import httpx
from pathlib import Path

from collector.core.models import Source
from collector.core.database import Database
from collector.core.state import StateManager
from collector.core.deduplication import DeduplicationEngine
from collector.sources.ats.ashby import AshbySource

FIXTURE_PATH = Path("tests/fixtures/ashby_response.json")

@pytest.fixture
def ashby_source():
    info = Source(
        source_id="ashby_linear",
        company_name="Linear",
        ats_platform="ashby",
        board_token="linear",
        base_url="https://api.ashbyhq.com/posting-api/job-board"
    )
    return AshbySource(info)

@pytest.fixture
def mock_fixture_data():
    if FIXTURE_PATH.exists():
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "jobs": [
            {
                "id": "ash-303",
                "title": "Software Engineer - Systems",
                "publishedAt": "2026-09-20T10:00:00Z",
                "jobUrl": "https://jobs.ashbyhq.com/linear/ash-303",
                "location": "San Francisco",
                "isRemote": True,
                "descriptionPlain": "Java microservices engineering role."
            }
        ]
    }

@pytest.mark.asyncio
async def test_ashby_fetch_success(ashby_source, mock_fixture_data):
    def handler(request):
        return httpx.Response(200, json=mock_fixture_data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ashby_source._client = client
        res = await ashby_source.fetch_jobs()

    assert res.is_success
    assert res.status_code == 200
    assert len(res.jobs) > 0

    job = res.jobs[0]
    assert job.company == "Linear"
    assert job.source == "ashby_linear"
    assert job.source_type == "ATS_DIRECT"
    assert job.posted_at is not None
    assert job.freshness_confidence == "HIGH"

@pytest.mark.asyncio
async def test_ashby_404_handling(ashby_source):
    def handler(request):
        return httpx.Response(404, json={"error": "Not Found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ashby_source._client = client
        res = await ashby_source.fetch_jobs()

    assert not res.is_success
    assert res.status_code == 404

def test_ashby_pipeline_idempotency(tmp_path):
    db = Database(tmp_path / "test.db")
    state_mgr = StateManager(tmp_path / "state")

    info = Source(source_id="ashby_linear", company_name="Linear", ats_platform="ashby", board_token="linear", base_url="")
    adapter = AshbySource(info)

    raw_job = {
        "id": "ash-404",
        "title": "Backend Tech Lead",
        "publishedAt": "2026-09-25T10:00:00Z",
        "jobUrl": "https://jobs.ashbyhq.com/linear/ash-404",
        "descriptionPlain": "Building high performance Java services."
    }

    job1 = adapter.parse_ashby_job(raw_job)
    p1, _ = DeduplicationEngine.process_job(job1, db, state_mgr)
    db.save_job(p1)

    assert p1.is_new is True
    t1 = p1.first_seen_at

    job2 = adapter.parse_ashby_job(raw_job)
    p2, is_changed = DeduplicationEngine.process_job(job2, db, state_mgr)
    db.save_job(p2)

    assert p2.is_new is False
    assert is_changed is False
    assert p2.first_seen_at == t1
