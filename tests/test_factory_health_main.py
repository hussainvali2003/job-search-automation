import pytest
import sys
from unittest.mock import patch, AsyncMock
from collector.core.models import Source, CollectorRun
from collector.sources.factory import create_adapter
from collector.sources.ats.greenhouse import GreenhouseSource
from collector.sources.ats.lever import LeverSource
from collector.sources.ats.ashby import AshbySource
from collector.sources.base import MockSource
from collector.sources.health import HealthTracker
from collector.main import main, main_async

def test_create_adapter():
    gh_source = Source(source_id="s1", company_name="C1", ats_platform="greenhouse", board_token="b1", base_url="")
    lev_source = Source(source_id="s2", company_name="C2", ats_platform="lever", board_token="b2", base_url="")
    ash_source = Source(source_id="s3", company_name="C3", ats_platform="ashby", board_token="b3", base_url="")
    mock_source = Source(source_id="s4", company_name="C4", ats_platform="custom", board_token="b4", base_url="")

    assert isinstance(create_adapter(gh_source), GreenhouseSource)
    assert isinstance(create_adapter(lev_source), LeverSource)
    assert isinstance(create_adapter(ash_source), AshbySource)
    assert isinstance(create_adapter(mock_source), MockSource)

def test_health_tracker():
    s = Source(source_id="test_h", company_name="Test", ats_platform="mock", board_token="test", base_url="")
    HealthTracker.record_success(s, duration_ms=100.0, jobs_count=10, relevant_count=5, fresh_count=2)
    
    assert s.total_requests_30d == 1
    assert s.successful_requests_30d == 1
    assert s.consecutive_failures == 0
    assert s.total_jobs_fetched_30d == 10
    assert s.relevant_jobs_30d == 5
    assert s.fresh_jobs_30d == 2

    HealthTracker.record_failure(s, duration_ms=200.0, error_msg="Timeout")
    assert s.total_requests_30d == 2
    assert s.failed_requests_30d == 1
    assert s.consecutive_failures == 1
    assert s.health_status == "ERROR"

@pytest.mark.asyncio
async def test_main_async_dry_run(monkeypatch):
    test_args = ["main.py", "--dry-run", "--tier", "P0"]
    monkeypatch.setattr(sys, "argv", test_args)
    await main_async()
