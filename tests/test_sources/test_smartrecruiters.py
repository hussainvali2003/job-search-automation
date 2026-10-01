import json
import pytest
import httpx
from pathlib import Path
from collector.core.models import Source
from collector.sources.ats.smartrecruiters import SmartRecruitersSource

FIXTURE_PATH = Path("tests/fixtures/smartrecruiters_response.json")

@pytest.fixture
def sr_source():
    info = Source(source_id="sr_bosch", company_name="Bosch", ats_platform="smartrecruiters", board_token="BoschGroup", base_url="")
    return SmartRecruitersSource(info)

@pytest.fixture
def mock_fixture_data():
    if FIXTURE_PATH.exists():
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"content": [{"id": "sr-101", "name": "Senior Java Developer", "releasedDate": "2026-09-25T10:00:00.000Z"}]}

@pytest.mark.asyncio
async def test_smartrecruiters_fetch_success(sr_source, mock_fixture_data):
    def handler(request):
        return httpx.Response(200, json=mock_fixture_data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        sr_source._client = client
        res = await sr_source.fetch_jobs()

    assert res.is_success
    assert res.status_code == 200
    assert len(res.jobs) > 0
    job = res.jobs[0]
    assert job.company == "Bosch"
    assert job.posted_at is not None
    assert job.freshness_confidence == "HIGH"
