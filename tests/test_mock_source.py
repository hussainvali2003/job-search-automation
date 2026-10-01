import pytest
from collector.core.models import Source
from collector.sources.base import MockSource

@pytest.mark.asyncio
async def test_mock_source_successful_fetch():
    source_info = Source(
        source_id="test_mock",
        company_name="MockCorp",
        ats_platform="greenhouse",
        board_token="mock",
        base_url="http://example.com"
    )
    mock_src = MockSource(source_info)
    
    assert mock_src.source_name() == "test_mock"
    assert mock_src.supports_timestamp() is True
    assert mock_src.freshness_confidence_level() == "HIGH"
    
    is_healthy = await mock_src.health_check()
    assert is_healthy is True
    
    result = await mock_src.fetch_jobs()
    assert result.is_success is True
    assert len(result.jobs) == 2
    assert result.jobs[0].company == "MockCorp"

@pytest.mark.asyncio
async def test_mock_source_failure_fetch():
    source_info = Source(
        source_id="test_failing",
        company_name="FailingCorp",
        ats_platform="lever",
        board_token="fail",
        base_url="http://example.com"
    )
    mock_src = MockSource(source_info, should_fail=True)
    
    is_healthy = await mock_src.health_check()
    assert is_healthy is False
    
    result = await mock_src.fetch_jobs()
    assert result.is_success is False
    assert result.status_code == 500
    assert "Mock HTTP 500" in result.error_message
