import pytest
from pathlib import Path
from collector.core.config import load_config, ConfigError

def test_load_valid_config():
    cfg = load_config("config")
    assert cfg.profile["user"]["name"] == "Java Developer"
    assert "Java" in cfg.profile["user"]["skills_primary"]
    assert cfg.scoring["weights"]["title_match"] == 0.35
    assert cfg.sources["tiers"]["P0"]["interval_minutes"] == 15
    assert cfg.filters["min_relevance_score"] == 0.40

def test_missing_config_raises_error(tmp_path):
    with pytest.raises(ConfigError, match="Required configuration file missing"):
        load_config(tmp_path)
