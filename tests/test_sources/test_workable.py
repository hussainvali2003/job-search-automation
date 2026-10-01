import json
import pytest
import httpx
from pathlib import Path
from collector.core.models import Source
from collector.sources.ats.workable import WorkableSource

FIXTURE_PATH = Path("tests/fixtures/workable_response.json")

@pytest.fixture
def workable_source():
    info = Source(source_id="workable_skroutz", company_name="Skroutz", ats_platform="workable", board_token="skroutz", base_url="")
    return WorkableSource(info)

@pytest.fixture
def mock_fixture_data():
    if FIXTURE_PATH.exists():
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"results": [{"shortcode": "W101", "title": "Java Backend Engineer", "published": "2026-09-25T10:00:00Z"}]}

@pytest.mark.asyncio
async def test_workable_fetch_success(workable_source, mock_fixture_data):
    def handler(request):
        return httpx.Response(200, json=mock_fixture_data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        workable_source._client = client
        res = await workable_source.fetch_jobs()

    assert res.is_success
    assert res.status_code == 200
    assert len(res.jobs) > 0
    job = res.jobs[0]
    assert job.company == "Skroutz"
    assert job.posted_at is not None
    assert job.freshness_confidence == "HIGH"
