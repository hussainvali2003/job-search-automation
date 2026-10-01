import json
from pathlib import Path
from typing import Optional
from collector.core.models import Source, iso_now
from collector.core.logger import logger

class SourceRegistry:
    def __init__(self, registry_file: str | Path = "data/source_registry.json"):
        self.registry_file = Path(registry_file)
        self.sources: list[Source] = []
        self.version: int = 2
        self.generated_at: str = iso_now()
        self.load_registry()

    def load_registry(self) -> None:
        """Loads registry JSON from disk."""
        if not self.registry_file.exists():
            logger.warning(f"Registry file not found at {self.registry_file}. Initializing empty.")
            self.sources = []
            return

        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.version = data.get("version", 2)
                self.generated_at = data.get("generated_at", iso_now())
                raw_sources = data.get("sources", [])
                self.sources = [Source.from_dict(s) for s in raw_sources if isinstance(s, dict)]
        except Exception as e:
            logger.error(f"Failed to load registry file {self.registry_file}: {e}")
            raise IOError(f"Invalid source registry file {self.registry_file}: {e}")

    def get_sources(self, tier: Optional[str] = None, enabled_only: bool = True) -> list[Source]:
        """Returns filtered list of registered sources."""
        result = []
        for s in self.sources:
            if enabled_only and not s.is_enabled:
                continue
            if tier and s.tier != tier:
                continue
            result.append(s)
        return result

    def get_source_by_id(self, source_id: str) -> Optional[Source]:
        for s in self.sources:
            if s.source_id == source_id:
                return s
        return None

    def add_or_update_source(self, source: Source) -> None:
        existing = self.get_source_by_id(source.source_id)
        if existing:
            # Update fields
            idx = self.sources.index(existing)
            self.sources[idx] = source
        else:
            self.sources.append(source)

    def save_registry(self) -> None:
        """Saves current sources back to source_registry.json."""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": self.version,
            "generated_at": iso_now(),
            "sources": [s.to_dict() for s in self.sources]
        }
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
