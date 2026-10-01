from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional
import uuid

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None

def format_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


@dataclass
class Job:
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Source Provenance
    source: str = ""                         # e.g. "greenhouse", "lever", "jobhive"
    source_type: str = "ATS_DIRECT"          # "ATS_DIRECT", "ATS_DATASET_SNAPSHOT", "RSS", "COMMUNITY"
    source_job_id: str = ""                  # Platform/employer job ID
    source_url: str = ""                     # Job posting URL
    
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    posted_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    first_seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    dataset_snapshot_at: Optional[datetime] = None
    freshness_confidence: str = "HIGH"      # "HIGH", "MEDIUM", "LOW", "SNAPSHOT_ONLY", "DISCOVERY_TIME_ONLY"
    
    # Company & Role
    company: str = ""
    company_normalized: str = ""
    title: str = ""
    title_normalized: str = ""
    employment_type: Optional[str] = None    # "FULL_TIME", "CONTRACT", etc.
    
    # Location & Compensation
    location: Optional[str] = None
    country: Optional[str] = None
    remote: Optional[bool] = None
    
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = None
    
    # Content
    description: Optional[str] = None
    description_snippet: Optional[str] = None
    skills: list[str] = field(default_factory=list)
    canonical_url: str = ""
    content_hash: str = ""
    
    # Status & Freshness
    status: str = "ACTIVE"                   # "ACTIVE", "CLOSED", "UNKNOWN"
    freshness_class: str = "UNKNOWN"         # "<6h", "<12h", "<24h", "1-3d", "3-7d", ">7d", "UNKNOWN"
    
    # Scoring
    relevance_score: Optional[float] = None
    personal_score: Optional[float] = None
    
    # Flags
    is_new: bool = True
    is_repost: bool = False
    duplicate_group_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.company_normalized and self.company:
            self.company_normalized = self.company.lower().strip()
        if not self.title_normalized and self.title:
            self.title_normalized = self.title.lower().strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "source_type": self.source_type,
            "source_job_id": self.source_job_id,
            "source_url": self.source_url,
            "fetched_at": format_iso(self.fetched_at),
            "posted_at": format_iso(self.posted_at),
            "updated_at": format_iso(self.updated_at),
            "first_seen_at": format_iso(self.first_seen_at),
            "last_seen_at": format_iso(self.last_seen_at),
            "last_verified_at": format_iso(self.last_verified_at),
            "dataset_snapshot_at": format_iso(self.dataset_snapshot_at),
            "freshness_confidence": self.freshness_confidence,
            "company": self.company,
            "company_normalized": self.company_normalized or self.company.lower().strip(),
            "title": self.title,
            "title_normalized": self.title_normalized or self.title.lower().strip(),
            "employment_type": self.employment_type,
            "location": self.location,
            "country": self.country,
            "remote": self.remote,
            "experience_min": self.experience_min,
            "experience_max": self.experience_max,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "currency": self.currency,
            "description": self.description,
            "description_snippet": self.description_snippet or (self.description[:500] if self.description else None),
            "skills": self.skills,
            "canonical_url": self.canonical_url,
            "content_hash": self.content_hash,
            "status": self.status,
            "freshness_class": self.freshness_class,
            "relevance_score": self.relevance_score,
            "personal_score": self.personal_score,
            "is_new": self.is_new,
            "is_repost": self.is_repost,
            "duplicate_group_id": self.duplicate_group_id,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Job":
        now = datetime.now(timezone.utc)
        return cls(
            id=d.get("id") or str(uuid.uuid4()),
            source=d.get("source", ""),
            source_type=d.get("source_type", "ATS_DIRECT"),
            source_job_id=str(d.get("source_job_id", "")),
            source_url=d.get("source_url", ""),
            fetched_at=parse_iso(d.get("fetched_at")) or now,
            posted_at=parse_iso(d.get("posted_at")),
            updated_at=parse_iso(d.get("updated_at")),
            first_seen_at=parse_iso(d.get("first_seen_at")) or now,
            last_seen_at=parse_iso(d.get("last_seen_at")) or now,
            last_verified_at=parse_iso(d.get("last_verified_at")) or now,
            dataset_snapshot_at=parse_iso(d.get("dataset_snapshot_at")),
            freshness_confidence=d.get("freshness_confidence", "HIGH"),
            company=d.get("company", ""),
            company_normalized=d.get("company_normalized", ""),
            title=d.get("title", ""),
            title_normalized=d.get("title_normalized", ""),
            employment_type=d.get("employment_type"),
            location=d.get("location"),
            country=d.get("country"),
            remote=d.get("remote"),
            experience_min=d.get("experience_min"),
            experience_max=d.get("experience_max"),
            salary_min=d.get("salary_min"),
            salary_max=d.get("salary_max"),
            currency=d.get("currency"),
            description=d.get("description"),
            description_snippet=d.get("description_snippet"),
            skills=d.get("skills", []),
            canonical_url=d.get("canonical_url", ""),
            content_hash=d.get("content_hash", ""),
            status=d.get("status", "ACTIVE"),
            freshness_class=d.get("freshness_class", "UNKNOWN"),
            relevance_score=d.get("relevance_score"),
            personal_score=d.get("personal_score"),
            is_new=d.get("is_new", True),
            is_repost=d.get("is_repost", False),
            duplicate_group_id=d.get("duplicate_group_id"),
        )


@dataclass
class Source:
    source_id: str                          # e.g. "greenhouse_infosys"
    company_name: str                       # e.g. "Infosys"
    ats_platform: str                       # e.g. "greenhouse", "lever", "ashby"
    board_token: str                        # e.g. "infosys"
    base_url: str                           # API endpoint base URL
    
    tier: str = "P2"                        # "P0", "P1", "P2", "P3"
    poll_interval_minutes: int = 360        # 15m (P0), 60m (P1), 360m (P2), 10080m (P3)
    is_enabled: bool = True
    
    source_value_score: float = 50.0        # Range 0.0 - 100.0
    
    # 30-Day Historical Metrics
    relevant_jobs_30d: int = 0
    fresh_jobs_30d: int = 0
    total_jobs_fetched_30d: int = 0
    duplicate_jobs_30d: int = 0
    
    total_requests_30d: int = 0
    successful_requests_30d: int = 0
    failed_requests_30d: int = 0
    consecutive_failures: int = 0
    avg_response_time_ms: float = 0.0
    
    health_status: str = "OK"               # "OK", "WARN", "SUSPECTED_BROKEN", "DISABLED"
    registry_source: str = "seed"           # "seed", "ats_scrapers_csv", "auto_discovery"
    last_fetched_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_tier_evaluated_at: Optional[datetime] = None

    def calculate_score(self) -> float:
        """Calculates and updates source_value_score based on historical metrics."""
        if self.total_requests_30d == 0:
            return self.source_value_score

        success_rate = self.successful_requests_30d / self.total_requests_30d
        failure_rate = self.failed_requests_30d / self.total_requests_30d
        dup_rate = (self.duplicate_jobs_30d / self.total_jobs_fetched_30d) if self.total_jobs_fetched_30d > 0 else 0.0
        
        s_yield = min(100.0, self.relevant_jobs_30d * 10.0)
        s_fresh = min(100.0, self.fresh_jobs_30d * 15.0)
        s_rel = success_rate * 100.0
        
        raw_score = (0.40 * s_yield) + (0.30 * s_fresh) + (0.30 * s_rel) - (0.50 * failure_rate * 100.0) - (0.20 * dup_rate * 100.0)
        self.source_value_score = max(0.0, min(100.0, raw_score))
        return self.source_value_score

    def evaluate_tier_promotion(self) -> str:
        """Determines target tier based on source_value_score and failure history."""
        score = self.calculate_score()
        if self.consecutive_failures >= 10:
            self.tier = "P3"
            self.health_status = "SUSPECTED_BROKEN"
            self.poll_interval_minutes = 10080
        elif self.consecutive_failures >= 3:
            self.tier = "P2"
            self.health_status = "WARN"
            self.poll_interval_minutes = 360
        elif score >= 75.0 and self.relevant_jobs_30d >= 2:
            self.tier = "P0"
            self.health_status = "OK"
            self.poll_interval_minutes = 15
        elif score >= 40.0:
            self.tier = "P1"
            self.health_status = "OK"
            self.poll_interval_minutes = 60
        elif score >= 15.0:
            self.tier = "P2"
            self.health_status = "OK"
            self.poll_interval_minutes = 360
        else:
            self.tier = "P3"
            self.health_status = "OK"
            self.poll_interval_minutes = 10080
        self.last_tier_evaluated_at = datetime.now(timezone.utc)
        return self.tier

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "company_name": self.company_name,
            "ats_platform": self.ats_platform,
            "board_token": self.board_token,
            "base_url": self.base_url,
            "tier": self.tier,
            "poll_interval_minutes": self.poll_interval_minutes,
            "is_enabled": self.is_enabled,
            "source_value_score": round(self.source_value_score, 2),
            "relevant_jobs_30d": self.relevant_jobs_30d,
            "fresh_jobs_30d": self.fresh_jobs_30d,
            "total_jobs_fetched_30d": self.total_jobs_fetched_30d,
            "duplicate_jobs_30d": self.duplicate_jobs_30d,
            "total_requests_30d": self.total_requests_30d,
            "successful_requests_30d": self.successful_requests_30d,
            "failed_requests_30d": self.failed_requests_30d,
            "consecutive_failures": self.consecutive_failures,
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "health_status": self.health_status,
            "registry_source": self.registry_source,
            "last_fetched_at": format_iso(self.last_fetched_at),
            "last_success_at": format_iso(self.last_success_at),
            "last_tier_evaluated_at": format_iso(self.last_tier_evaluated_at),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Source":
        return cls(
            source_id=d.get("source_id", ""),
            company_name=d.get("company_name", ""),
            ats_platform=d.get("ats_platform", ""),
            board_token=d.get("board_token", ""),
            base_url=d.get("base_url", ""),
            tier=d.get("tier", "P2"),
            poll_interval_minutes=d.get("poll_interval_minutes", 360),
            is_enabled=d.get("is_enabled", True),
            source_value_score=float(d.get("source_value_score", 50.0)),
            relevant_jobs_30d=int(d.get("relevant_jobs_30d", 0)),
            fresh_jobs_30d=int(d.get("fresh_jobs_30d", 0)),
            total_jobs_fetched_30d=int(d.get("total_jobs_fetched_30d", 0)),
            duplicate_jobs_30d=int(d.get("duplicate_jobs_30d", 0)),
            total_requests_30d=int(d.get("total_requests_30d", 0)),
            successful_requests_30d=int(d.get("successful_requests_30d", 0)),
            failed_requests_30d=int(d.get("failed_requests_30d", 0)),
            consecutive_failures=int(d.get("consecutive_failures", 0)),
            avg_response_time_ms=float(d.get("avg_response_time_ms", 0.0)),
            health_status=d.get("health_status", "OK"),
            registry_source=d.get("registry_source", "seed"),
            last_fetched_at=parse_iso(d.get("last_fetched_at")),
            last_success_at=parse_iso(d.get("last_success_at")),
            last_tier_evaluated_at=parse_iso(d.get("last_tier_evaluated_at")),
        )


@dataclass
class CollectorRun:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    tier_run: str = "P0"
    
    sources_polled: int = 0
    sources_successful: int = 0
    sources_failed: int = 0
    
    jobs_fetched: int = 0
    jobs_new: int = 0
    jobs_duplicates: int = 0
    status: str = "RUNNING"                 # "RUNNING", "COMPLETED", "FAILED"

    def finalize(self, status: str = "COMPLETED") -> None:
        self.finished_at = datetime.now(timezone.utc)
        self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
        self.status = status

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": format_iso(self.started_at),
            "finished_at": format_iso(self.finished_at),
            "duration_seconds": round(self.duration_seconds, 2),
            "tier_run": self.tier_run,
            "sources_polled": self.sources_polled,
            "sources_successful": self.sources_successful,
            "sources_failed": self.sources_failed,
            "jobs_fetched": self.jobs_fetched,
            "jobs_new": self.jobs_new,
            "jobs_duplicates": self.jobs_duplicates,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CollectorRun":
        now = datetime.now(timezone.utc)
        return cls(
            run_id=d.get("run_id") or str(uuid.uuid4()),
            started_at=parse_iso(d.get("started_at")) or now,
            finished_at=parse_iso(d.get("finished_at")),
            duration_seconds=float(d.get("duration_seconds", 0.0)),
            tier_run=d.get("tier_run", "P0"),
            sources_polled=int(d.get("sources_polled", 0)),
            sources_successful=int(d.get("sources_successful", 0)),
            sources_failed=int(d.get("sources_failed", 0)),
            jobs_fetched=int(d.get("jobs_fetched", 0)),
            jobs_new=int(d.get("jobs_new", 0)),
            jobs_duplicates=int(d.get("jobs_duplicates", 0)),
            status=d.get("status", "RUNNING"),
        )


@dataclass
class UserAction:
    """Local-only model for tracking user interactions (SAVED, APPLIED, DISMISSED)."""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = ""
    action_type: str = "SAVED"              # "SAVED", "APPLIED", "DISMISSED", "INTERVIEW"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "job_id": self.job_id,
            "action_type": self.action_type,
            "timestamp": format_iso(self.timestamp),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "UserAction":
        return cls(
            action_id=d.get("action_id") or str(uuid.uuid4()),
            job_id=d.get("job_id", ""),
            action_type=d.get("action_type", "SAVED"),
            timestamp=parse_iso(d.get("timestamp")) or datetime.now(timezone.utc),
            notes=d.get("notes"),
        )
