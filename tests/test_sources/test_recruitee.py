import json
import pytest
import httpx
from pathlib import Path
from collector.core.models import Source
from collector.sources.ats.recruitee import RecruiteeSource

FIXTURE_PATH = Path("tests/fixtures/recruitee_response.json")

@pytest.fixture
def recruitee_source():
    info = Source(source_id="rec_bunq", company_name="Bunq", ats_platform="recruitee", board_token="bunq", base_url="")
    return RecruiteeSource(info)

@pytest.fixture
def mock_fixture_data():
    if FIXTURE_PATH.exists():
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"offers": [{"id": "rec-101", "title": "Java Backend Developer", "published_at": "2026-09-25T10:00:00Z"}]}

@pytest.mark.asyncio
async def test_recruitee_fetch_success(recruitee_source, mock_fixture_data):
    def handler(request):
        return httpx.Response(200, json=mock_fixture_data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        recruitee_source._client = client
        res = await recruitee_source.fetch_jobs()

    assert res.is_success
    assert res.status_code == 200
    assert len(res.jobs) > 0
    job = res.jobs[0]
    assert job.company == "Bunq"
    assert job.posted_at is not None
    assert job.freshness_confidence == "HIGH"
