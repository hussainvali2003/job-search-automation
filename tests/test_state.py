import json
import pytest
from collector.core.state import StateManager
from collector.core.models import Source, CollectorRun

def test_state_manager_lifecycle(tmp_path):
    state_mgr = StateManager(state_dir=tmp_path)
    
    # 1. New ID check
    assert state_mgr.is_new("job-100") is True
    state_mgr.mark_seen(["job-100"])
    assert state_mgr.is_new("job-100") is False
    
    # 2. Source health update
    source = Source(source_id="src-100", company_name="CompX", ats_platform="greenhouse", board_token="compx", base_url="http://example.com")
    state_mgr.update_source_health(source)
    
    # 3. Add run summary
    run = CollectorRun(run_id="run-100", tier_run="P0", jobs_fetched=12, jobs_new=10)
    state_mgr.add_run_summary(run)
    
    # Save state
    state_mgr.save_state()
    
    # Reload in a new StateManager instance
    reloaded_state = StateManager(state_dir=tmp_path)
    assert reloaded_state.is_new("job-100") is False
    assert reloaded_state.is_new("job-200") is True
    assert "src-100" in reloaded_state.source_health
    assert len(reloaded_state.run_history) == 1
    assert reloaded_state.run_history[0]["run_id"] == "run-100"
