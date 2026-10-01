from pathlib import Path
from typing import Any
import yaml

class ConfigError(ValueError):
    """Raised when required configuration fields are missing or invalid."""
    pass

class Config:
    def __init__(self, config_dir: str | Path = "config"):
        self.config_dir = Path(config_dir)
        self.profile: dict[str, Any] = self._load_yaml("profile.yaml")
        self.scoring: dict[str, Any] = self._load_yaml("scoring.yaml")
        self.sources: dict[str, Any] = self._load_yaml("sources.yaml")
        self.filters: dict[str, Any] = self._load_yaml("filters.yaml")
        self._validate()

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise ConfigError(f"Required configuration file missing: {filepath}")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            raise ConfigError(f"Error parsing configuration file {filepath}: {e}")

    def _validate(self) -> None:
        user = self.profile.get("user")
        if not user or not isinstance(user, dict):
            raise ConfigError("profile.yaml must contain a 'user' dictionary")
        
        required_user_keys = ["name", "target_titles", "skills_primary", "locations_preferred"]
        for key in required_user_keys:
            if key not in user or not user[key]:
                raise ConfigError(f"profile.yaml user configuration missing required key: '{key}'")
        
        if "weights" not in self.scoring:
            raise ConfigError("scoring.yaml missing required 'weights' section")

def load_config(config_dir: str | Path = "config") -> Config:
    return Config(config_dir=config_dir)
