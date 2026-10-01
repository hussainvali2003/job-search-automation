from collector.sources.registry import SourceRegistry
from collector.core.models import Source

def test_load_and_filter_registry(tmp_path):
    registry_file = "data/source_registry.json"
    registry = SourceRegistry(registry_file)
    
    assert len(registry.sources) >= 3
    
    p0_sources = registry.get_sources(tier="P0")
    assert len(p0_sources) >= 2
    assert all(s.tier == "P0" for s in p0_sources)
    
    p1_sources = registry.get_sources(tier="P1")
    assert len(p1_sources) >= 1
    assert all(s.tier == "P1" for s in p1_sources)

def test_registry_save_roundtrip(tmp_path):
    target = tmp_path / "test_registry.json"
    registry = SourceRegistry("data/source_registry.json")
    registry.registry_file = target
    
    new_source = Source(
        source_id="test_new_source",
        company_name="NewCorp",
        ats_platform="ashby",
        board_token="newcorp",
        base_url="https://api.ashbyhq.com/posting-api/job-board/newcorp",
        tier="P1"
    )
    registry.add_or_update_source(new_source)
    registry.save_registry()
    
    reloaded = SourceRegistry(target)
    assert reloaded.get_source_by_id("test_new_source") is not None
    assert reloaded.get_source_by_id("test_new_source").company_name == "NewCorp"
