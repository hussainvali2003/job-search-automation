from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from collector.core.models import Job, Source

@dataclass
class FetchResult:
    jobs: list[Job] = field(default_factory=list)
    total_raw: int = 0
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    status_code: int = 200

    @property
    def is_success(self) -> bool:
        return self.status_code == 200 and self.error_message is None


class JobSource(ABC):
    def __init__(self, source_info: Source):
        self.source_info = source_info

    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier e.g. 'greenhouse_infosys'."""
        pass

    @abstractmethod
    def source_type(self) -> str:
        """'ATS_DIRECT', 'ATS_DATASET_SNAPSHOT', 'RSS', etc."""
        pass

    @abstractmethod
    def ats_platform(self) -> str:
        """'greenhouse', 'lever', 'ashby', 'workable', etc."""
        pass

    @abstractmethod
    async def fetch_jobs(self) -> FetchResult:
        """Fetches jobs asynchronously from the source endpoint."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Performs endpoint health verification."""
        pass

    @abstractmethod
    def supports_timestamp(self) -> bool:
        """Returns True if this source explicitly provides employer posting timestamps."""
        pass

    @abstractmethod
    def freshness_confidence_level(self) -> str:
        """'HIGH', 'MEDIUM', 'LOW', 'SNAPSHOT_ONLY', or 'DISCOVERY_TIME_ONLY'."""
        pass


class MockSource(JobSource):
    """Test mock implementation returning static test jobs."""
    def __init__(self, source_info: Source, mock_jobs: Optional[list[Job]] = None, should_fail: bool = False):
        super().__init__(source_info)
        self.should_fail = should_fail
        self._mock_jobs = mock_jobs or [
            Job(
                source=self.source_name(),
                source_type=self.source_type(),
                source_job_id="mock-1",
                source_url="https://example.com/jobs/1",
                company="MockCorp",
                title="Java Backend Engineer",
                freshness_confidence="HIGH",
                posted_at=datetime.now(timezone.utc),
            ),
            Job(
                source=self.source_name(),
                source_type=self.source_type(),
                source_job_id="mock-2",
                source_url="https://example.com/jobs/2",
                company="MockCorp",
                title="Spring Boot Microservices Developer",
                freshness_confidence="HIGH",
                posted_at=datetime.now(timezone.utc),
            )
        ]

    def source_name(self) -> str:
        return self.source_info.source_id or "mock_source"

    def source_type(self) -> str:
        return "ATS_DIRECT"

    def ats_platform(self) -> str:
        return self.source_info.ats_platform or "mock"

    async def fetch_jobs(self) -> FetchResult:
        if self.should_fail:
            return FetchResult(
                jobs=[],
                total_raw=0,
                duration_ms=150.0,
                error_message="Mock HTTP 500 Connection Failed",
                status_code=500,
            )
        return FetchResult(
            jobs=self._mock_jobs,
            total_raw=len(self._mock_jobs),
            duration_ms=120.0,
            error_message=None,
            status_code=200,
        )

    async def health_check(self) -> bool:
        return not self.should_fail

    def supports_timestamp(self) -> bool:
        return True

    def freshness_confidence_level(self) -> str:
        return "HIGH"
