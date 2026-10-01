import json
from pathlib import Path
import sqlite3
from typing import Any, Optional
from datetime import datetime, timezone
from collector.core.models import Job, Source, CollectorRun, parse_iso, format_iso

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_job_id TEXT NOT NULL,
    source_url TEXT,
    fetched_at TEXT NOT NULL,
    posted_at TEXT,
    updated_at TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    last_verified_at TEXT NOT NULL,
    dataset_snapshot_at TEXT,
    freshness_confidence TEXT NOT NULL,
    company TEXT NOT NULL,
    company_normalized TEXT NOT NULL,
    title TEXT NOT NULL,
    title_normalized TEXT NOT NULL,
    employment_type TEXT,
    location TEXT,
    country TEXT,
    remote INTEGER,
    experience_min INTEGER,
    experience_max INTEGER,
    salary_min INTEGER,
    salary_max INTEGER,
    currency TEXT,
    description TEXT,
    description_snippet TEXT,
    skills_json TEXT,
    canonical_url TEXT,
    content_hash TEXT,
    status TEXT NOT NULL,
    freshness_class TEXT NOT NULL,
    relevance_score REAL,
    personal_score REAL,
    is_new INTEGER NOT NULL,
    is_repost INTEGER NOT NULL,
    duplicate_group_id TEXT
);

CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    ats_platform TEXT NOT NULL,
    board_token TEXT NOT NULL,
    base_url TEXT NOT NULL,
    tier TEXT NOT NULL,
    poll_interval_minutes INTEGER NOT NULL,
    is_enabled INTEGER NOT NULL,
    source_value_score REAL NOT NULL,
    relevant_jobs_30d INTEGER NOT NULL,
    fresh_jobs_30d INTEGER NOT NULL,
    total_jobs_fetched_30d INTEGER NOT NULL,
    duplicate_jobs_30d INTEGER NOT NULL,
    total_requests_30d INTEGER NOT NULL,
    successful_requests_30d INTEGER NOT NULL,
    failed_requests_30d INTEGER NOT NULL,
    consecutive_failures INTEGER NOT NULL,
    avg_response_time_ms REAL NOT NULL,
    health_status TEXT NOT NULL,
    registry_source TEXT NOT NULL,
    last_fetched_at TEXT,
    last_success_at TEXT,
    last_tier_evaluated_at TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    duration_seconds REAL NOT NULL,
    tier_run TEXT NOT NULL,
    sources_polled INTEGER NOT NULL,
    sources_successful INTEGER NOT NULL,
    sources_failed INTEGER NOT NULL,
    jobs_fetched INTEGER NOT NULL,
    jobs_new INTEGER NOT NULL,
    jobs_duplicates INTEGER NOT NULL,
    status TEXT NOT NULL
);
"""

class Database:
    def __init__(self, db_path: str | Path = ":memory:"):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.executescript(SCHEMA_SQL)

    def save_job(self, job: Job) -> None:
        """Upserts a job. Preserves original first_seen_at if existing."""
        d = job.to_dict()
        existing = self.get_job_by_id(job.id)
        first_seen = d["first_seen_at"]
        if existing and existing.first_seen_at:
            first_seen = format_iso(existing.first_seen_at)

        query = """
        INSERT INTO jobs (
            id, source, source_type, source_job_id, source_url,
            fetched_at, posted_at, updated_at, first_seen_at, last_seen_at,
            last_verified_at, dataset_snapshot_at, freshness_confidence,
            company, company_normalized, title, title_normalized,
            employment_type, location, country, remote,
            experience_min, experience_max, salary_min, salary_max, currency,
            description, description_snippet, skills_json, canonical_url,
            content_hash, status, freshness_class, relevance_score, personal_score,
            is_new, is_repost, duplicate_group_id
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        ) ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            title_normalized=excluded.title_normalized,
            company=excluded.company,
            company_normalized=excluded.company_normalized,
            description=excluded.description,
            description_snippet=excluded.description_snippet,
            source_url=excluded.source_url,
            last_seen_at=excluded.last_seen_at,
            last_verified_at=excluded.last_verified_at,
            status=excluded.status,
            freshness_class=excluded.freshness_class,
            relevance_score=excluded.relevance_score,
            personal_score=excluded.personal_score,
            is_new=excluded.is_new,
            is_repost=excluded.is_repost
        """
        params = (
            d["id"], d["source"], d["source_type"], d["source_job_id"], d["source_url"],
            d["fetched_at"], d["posted_at"], d["updated_at"], first_seen, d["last_seen_at"],
            d["last_verified_at"], d["dataset_snapshot_at"], d["freshness_confidence"],
            d["company"], d["company_normalized"], d["title"], d["title_normalized"],
            d["employment_type"], d["location"], d["country"], 1 if d["remote"] else 0,
            d["experience_min"], d["experience_max"], d["salary_min"], d["salary_max"], d["currency"],
            d["description"], d["description_snippet"], json.dumps(d["skills"]), d["canonical_url"],
            d["content_hash"], d["status"], d["freshness_class"], d["relevance_score"], d["personal_score"],
            1 if d["is_new"] else 0, 1 if d["is_repost"] else 0, d["duplicate_group_id"]
        )
        with self.conn:
            self.conn.execute(query, params)

    def get_job_by_id(self, job_id: str) -> Optional[Job]:
        cur = self.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cur.fetchone()
        if not row:
            return None
        return self._row_to_job(row)

    def get_jobs_by_source(self, source_name: str) -> list[Job]:
        cur = self.conn.execute("SELECT * FROM jobs WHERE source = ?", (source_name,))
        return [self._row_to_job(row) for row in cur.fetchall()]

    def get_jobs_by_company(self, company_norm: str) -> list[Job]:
        cur = self.conn.execute("SELECT * FROM jobs WHERE company_normalized = ?", (company_norm,))
        return [self._row_to_job(row) for row in cur.fetchall()]

    def mark_closed_jobs(self, active_job_ids: set[str], source_name: str) -> int:
        """Marks any job from source_name not in active_job_ids as CLOSED."""
        cur = self.conn.execute("SELECT id FROM jobs WHERE source = ? AND status = 'ACTIVE'", (source_name,))
        existing_ids = {row["id"] for row in cur.fetchall()}
        closed_ids = existing_ids - active_job_ids
        if not closed_ids:
            return 0
        with self.conn:
            self.conn.executemany(
                "UPDATE jobs SET status = 'CLOSED' WHERE id = ?",
                [(jid,) for jid in closed_ids]
            )
        return len(closed_ids)

    def save_source(self, source: Source) -> None:
        d = source.to_dict()
        query = """
        INSERT INTO sources (
            source_id, company_name, ats_platform, board_token, base_url,
            tier, poll_interval_minutes, is_enabled, source_value_score,
            relevant_jobs_30d, fresh_jobs_30d, total_jobs_fetched_30d, duplicate_jobs_30d,
            total_requests_30d, successful_requests_30d, failed_requests_30d,
            consecutive_failures, avg_response_time_ms, health_status, registry_source,
            last_fetched_at, last_success_at, last_tier_evaluated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        ) ON CONFLICT(source_id) DO UPDATE SET
            tier=excluded.tier,
            poll_interval_minutes=excluded.poll_interval_minutes,
            is_enabled=excluded.is_enabled,
            source_value_score=excluded.source_value_score,
            relevant_jobs_30d=excluded.relevant_jobs_30d,
            fresh_jobs_30d=excluded.fresh_jobs_30d,
            total_jobs_fetched_30d=excluded.total_jobs_fetched_30d,
            duplicate_jobs_30d=excluded.duplicate_jobs_30d,
            total_requests_30d=excluded.total_requests_30d,
            successful_requests_30d=excluded.successful_requests_30d,
            failed_requests_30d=excluded.failed_requests_30d,
            consecutive_failures=excluded.consecutive_failures,
            avg_response_time_ms=excluded.avg_response_time_ms,
            health_status=excluded.health_status,
            last_fetched_at=excluded.last_fetched_at,
            last_success_at=excluded.last_success_at,
            last_tier_evaluated_at=excluded.last_tier_evaluated_at
        """
        params = (
            d["source_id"], d["company_name"], d["ats_platform"], d["board_token"], d["base_url"],
            d["tier"], d["poll_interval_minutes"], 1 if d["is_enabled"] else 0, d["source_value_score"],
            d["relevant_jobs_30d"], d["fresh_jobs_30d"], d["total_jobs_fetched_30d"], d["duplicate_jobs_30d"],
            d["total_requests_30d"], d["successful_requests_30d"], d["failed_requests_30d"],
            d["consecutive_failures"], d["avg_response_time_ms"], d["health_status"], d["registry_source"],
            d["last_fetched_at"], d["last_success_at"], d["last_tier_evaluated_at"]
        )
        with self.conn:
            self.conn.execute(query, params)

    def save_run(self, run: CollectorRun) -> None:
        d = run.to_dict()
        query = """
        INSERT INTO runs (
            run_id, started_at, finished_at, duration_seconds, tier_run,
            sources_polled, sources_successful, sources_failed,
            jobs_fetched, jobs_new, jobs_duplicates, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            finished_at=excluded.finished_at,
            duration_seconds=excluded.duration_seconds,
            sources_polled=excluded.sources_polled,
            sources_successful=excluded.sources_successful,
            sources_failed=excluded.sources_failed,
            jobs_fetched=excluded.jobs_fetched,
            jobs_new=excluded.jobs_new,
            jobs_duplicates=excluded.jobs_duplicates,
            status=excluded.status
        """
        params = (
            d["run_id"], d["started_at"], d["finished_at"], d["duration_seconds"], d["tier_run"],
            d["sources_polled"], d["sources_successful"], d["sources_failed"],
            d["jobs_fetched"], d["jobs_new"], d["jobs_duplicates"], d["status"]
        )
        with self.conn:
            self.conn.execute(query, params)

    def _row_to_job(self, r: sqlite3.Row) -> Job:
        skills = []
        if r["skills_json"]:
            try:
                skills = json.loads(r["skills_json"])
            except Exception:
                pass
        return Job(
            id=r["id"],
            source=r["source"],
            source_type=r["source_type"],
            source_job_id=r["source_job_id"],
            source_url=r["source_url"] or "",
            fetched_at=parse_iso(r["fetched_at"]) or datetime.now(timezone.utc),
            posted_at=parse_iso(r["posted_at"]),
            updated_at=parse_iso(r["updated_at"]),
            first_seen_at=parse_iso(r["first_seen_at"]) or datetime.now(timezone.utc),
            last_seen_at=parse_iso(r["last_seen_at"]) or datetime.now(timezone.utc),
            last_verified_at=parse_iso(r["last_verified_at"]) or datetime.now(timezone.utc),
            dataset_snapshot_at=parse_iso(r["dataset_snapshot_at"]),
            freshness_confidence=r["freshness_confidence"],
            company=r["company"],
            company_normalized=r["company_normalized"],
            title=r["title"],
            title_normalized=r["title_normalized"],
            employment_type=r["employment_type"],
            location=r["location"],
            country=r["country"],
            remote=bool(r["remote"]),
            experience_min=r["experience_min"],
            experience_max=r["experience_max"],
            salary_min=r["salary_min"],
            salary_max=r["salary_max"],
            currency=r["currency"],
            description=r["description"],
            description_snippet=r["description_snippet"],
            skills=skills,
            canonical_url=r["canonical_url"] or "",
            content_hash=r["content_hash"] or "",
            status=r["status"],
            freshness_class=r["freshness_class"],
            relevance_score=r["relevance_score"],
            personal_score=r["personal_score"],
            is_new=bool(r["is_new"]),
            is_repost=bool(r["is_repost"]),
            duplicate_group_id=r["duplicate_group_id"],
        )

    def close(self) -> None:
        if self.conn:
            self.conn.close()
