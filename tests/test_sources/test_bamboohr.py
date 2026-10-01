import json
import pytest
import httpx
from pathlib import Path
from collector.core.models import Source
from collector.sources.ats.bamboohr import BambooHRSource

FIXTURE_PATH = Path("tests/fixtures/bamboohr_response.json")

@pytest.fixture
def bamboohr_source():
    info = Source(source_id="bamboo_test", company_name="TestCorp", ats_platform="bamboohr", board_token="company", base_url="")
    return BambooHRSource(info)

@pytest.fixture
def mock_fixture_data():
    if FIXTURE_PATH.exists():
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"result": [{"id": "bam-101", "jobTitle": "Java Software Engineer", "datePosted": "2026-09-25"}]}

@pytest.mark.asyncio
async def test_bamboohr_fetch_success(bamboohr_source, mock_fixture_data):
    def handler(request):
        return httpx.Response(200, json=mock_fixture_data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        bamboohr_source._client = client
        res = await bamboohr_source.fetch_jobs()

    assert res.is_success
    assert res.status_code == 200
    assert len(res.jobs) > 0
    job = res.jobs[0]
    assert job.company == "TestCorp"
    assert job.posted_at is not None
    assert job.freshness_confidence == "HIGH"
