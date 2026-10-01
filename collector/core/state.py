import json
from pathlib import Path
import os
import tempfile
from typing import Any, Optional, Set
from collector.core.models import Source, CollectorRun, iso_now
from collector.core.logger import logger

class StateManager:
    def __init__(self, state_dir: str | Path = "state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.seen_ids_file = self.state_dir / "seen_ids.json"
        self.source_health_file = self.state_dir / "source_health.json"
        self.run_history_file = self.state_dir / "run_history.json"
        
        self.seen_ids: Set[str] = set()
        self.source_health: dict[str, dict[str, Any]] = {}
        self.run_history: list[dict[str, Any]] = []
        
        self.load_state()

    def load_state(self) -> None:
        """Loads state files from state_dir if present."""
        # 1. Seen IDs
        if self.seen_ids_file.exists():
            try:
                with open(self.seen_ids_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.seen_ids = set(data)
            except Exception as e:
                logger.warning(f"Failed to load seen_ids.json: {e}")
                self.seen_ids = set()

        # 2. Source Health
        if self.source_health_file.exists():
            try:
                with open(self.source_health_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.source_health = data
            except Exception as e:
                logger.warning(f"Failed to load source_health.json: {e}")
                self.source_health = {}

        # 3. Run History
        if self.run_history_file.exists():
            try:
                with open(self.run_history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.run_history = data
            except Exception as e:
                logger.warning(f"Failed to load run_history.json: {e}")
                self.run_history = []

    def is_new(self, job_id: str) -> bool:
        """Returns True if job_id has never been seen before."""
        return job_id not in self.seen_ids

    def mark_seen(self, job_ids: list[str] | set[str]) -> None:
        """Adds job_ids to the seen set."""
        self.seen_ids.update(job_ids)

    def update_source_health(self, source: Source) -> None:
        """Updates health record for a single source."""
        self.source_health[source.source_id] = source.to_dict()

    def add_run_summary(self, run: CollectorRun) -> None:
        """Appends run summary to history and caps at 100 recent runs."""
        self.run_history.append(run.to_dict())
        if len(self.run_history) > 100:
            self.run_history = self.run_history[-100:]

    def save_state(self) -> None:
        """Atomically saves state files."""
        self._atomic_write_json(self.seen_ids_file, sorted(list(self.seen_ids)))
        self._atomic_write_json(self.source_health_file, self.source_health)
        self._atomic_write_json(self.run_history_file, self.run_history)

    def _atomic_write_json(self, filepath: Path, content: Any) -> None:
        """Writes JSON to a temporary file and atomically renames it."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        temp_fd, temp_path = tempfile.mkstemp(dir=filepath.parent, prefix=".tmp_state_", suffix=".json")
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2)
            os.replace(temp_path, filepath)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise IOError(f"Failed to atomically write state file {filepath}: {e}")
