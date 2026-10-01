import time
import httpx
from datetime import datetime, timezone
from typing import Optional

from collector.core.models import Job, Source, parse_iso
from collector.sources.base import JobSource, FetchResult
from collector.core.normalization import clean_html, extract_skills, compute_content_hash
from collector.core.freshness import calculate_freshness_class
from collector.core.provenance import generate_job_id, build_canonical_url

GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"

class GreenhouseSource(JobSource):
    """
    Direct collector for public Greenhouse job boards via REST API.
    API Endpoint: GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
    """

    def __init__(self, source_info: Source, client: Optional[httpx.AsyncClient] = None):
        super().__init__(source_info)
        self._client = client

    def source_name(self) -> str:
        return self.source_info.source_id or f"greenhouse_{self.source_info.board_token}"

    def source_type(self) -> str:
        return "ATS_DIRECT"

    def ats_platform(self) -> str:
        return "greenhouse"

    def supports_timestamp(self) -> bool:
        return True

    def freshness_confidence_level(self) -> str:
        return "MEDIUM"

    async def fetch_jobs(self) -> FetchResult:
        board_token = self.source_info.board_token
        url = f"{GREENHOUSE_API_BASE}/{board_token}/jobs?content=true"
        start_time = time.monotonic()

        headers = {
            "User-Agent": "JobRadarCollector/1.0 (+https://github.com/job-radar)",
            "Accept": "application/json"
        }

        should_close = False
        client = self._client
        if client is None:
            client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
            should_close = True

        try:
            resp = await client.get(url, headers=headers)
            duration_ms = (time.monotonic() - start_time) * 1000.0

            if resp.status_code != 200:
                return FetchResult(
                    jobs=[],
                    total_raw=0,
                    duration_ms=duration_ms,
                    error_message=f"HTTP {resp.status_code}: {resp.reason_phrase}",
                    status_code=resp.status_code
                )

            try:
                data = resp.json()
            except Exception as e:
                return FetchResult(
                    jobs=[],
                    total_raw=0,
                    duration_ms=duration_ms,
                    error_message=f"Malformed JSON response: {e}",
                    status_code=200
                )

            raw_jobs = data.get("jobs", [])
            parsed_jobs = []

            for raw_job in raw_jobs:
                job_obj = self.parse_greenhouse_job(raw_job)
                if job_obj:
                    parsed_jobs.append(job_obj)

            return FetchResult(
                jobs=parsed_jobs,
                total_raw=len(raw_jobs),
                duration_ms=duration_ms,
                error_message=None,
                status_code=200
            )

        except httpx.TimeoutException:
            duration_ms = (time.monotonic() - start_time) * 1000.0
            return FetchResult(
                jobs=[],
                total_raw=0,
                duration_ms=duration_ms,
                error_message="HTTP Request Timeout",
                status_code=408
            )
        except Exception as e:
            duration_ms = (time.monotonic() - start_time) * 1000.0
            return FetchResult(
                jobs=[],
                total_raw=0,
                duration_ms=duration_ms,
                error_message=f"Network Error: {e}",
                status_code=500
            )
        finally:
            if should_close:
                await client.aclose()

    def parse_greenhouse_job(self, raw_job: dict) -> Optional[Job]:
        raw_id = str(raw_job.get("id", ""))
        if not raw_id:
            return None

        title = raw_job.get("title", "").strip()
        if not title:
            return None

        job_id = generate_job_id(self.source_name(), raw_id)
        
        # Exact Greenhouse timestamp fields
        updated_at_str = raw_job.get("updated_at")
        updated_at = parse_iso(updated_at_str)

        # Greenhouse public API provides updated_at, and sometimes first_published / posted_at / created_at.
        # We do NOT invent posted_at if no employer date field is present.
        posted_at = None
        if "first_published" in raw_job and raw_job["first_published"]:
            posted_at = parse_iso(raw_job["first_published"])
        elif "posted_at" in raw_job and raw_job["posted_at"]:
            posted_at = parse_iso(raw_job["posted_at"])
        elif "created_at" in raw_job and raw_job["created_at"]:
            posted_at = parse_iso(raw_job["created_at"])

        confidence = "HIGH" if posted_at is not None else "MEDIUM"
        freshness_cls = calculate_freshness_class(posted_at, updated_at)

        source_url = raw_job.get("absolute_url", "")
        canonical_url = build_canonical_url(source_url)

        loc_dict = raw_job.get("location")
        location = loc_dict.get("name") if isinstance(loc_dict, dict) else None

        raw_content = raw_job.get("content", "")
        description = clean_html(raw_content)
        snippet = description[:500] if description else None
        skills = extract_skills(f"{title} {description}")

        company = self.source_info.company_name or "Unknown Company"
        content_hash = compute_content_hash(company, title, description)

        now = datetime.now(timezone.utc)

        return Job(
            id=job_id,
            source=self.source_name(),
            source_type="ATS_DIRECT",
            source_job_id=raw_id,
            source_url=source_url,
            fetched_at=now,
            posted_at=posted_at,
            updated_at=updated_at,
            first_seen_at=now,
            last_seen_at=now,
            last_verified_at=now,
            freshness_confidence=confidence,
            company=company,
            title=title,
            location=location,
            description=description,
            description_snippet=snippet,
            skills=skills,
            canonical_url=canonical_url,
            content_hash=content_hash,
            freshness_class=freshness_cls,
            status="ACTIVE",
            is_new=True
        )

    async def health_check(self) -> bool:
        res = await self.fetch_jobs()
        return res.is_success
