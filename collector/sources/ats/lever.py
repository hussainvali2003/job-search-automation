import time
import httpx
from datetime import datetime, timezone
from typing import Optional

from collector.core.models import Job, Source
from collector.sources.base import JobSource, FetchResult
from collector.core.normalization import clean_html, extract_skills, compute_content_hash
from collector.core.freshness import calculate_freshness_class
from collector.core.provenance import generate_job_id, build_canonical_url

LEVER_API_BASE = "https://api.lever.co/v0/postings"

class LeverSource(JobSource):
    """
    Direct collector for public Lever job postings via REST API.
    API Endpoint: GET https://api.lever.co/v0/postings/{company}?mode=json
    """

    def __init__(self, source_info: Source, client: Optional[httpx.AsyncClient] = None):
        super().__init__(source_info)
        self._client = client

    def source_name(self) -> str:
        return self.source_info.source_id or f"lever_{self.source_info.board_token}"

    def source_type(self) -> str:
        return "ATS_DIRECT"

    def ats_platform(self) -> str:
        return "lever"

    def supports_timestamp(self) -> bool:
        return True

    def freshness_confidence_level(self) -> str:
        return "HIGH"

    async def fetch_jobs(self) -> FetchResult:
        board_token = self.source_info.board_token
        url = f"{LEVER_API_BASE}/{board_token}?mode=json"
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

            if not isinstance(data, list):
                return FetchResult(
                    jobs=[],
                    total_raw=0,
                    duration_ms=duration_ms,
                    error_message="Unexpected JSON structure (expected list)",
                    status_code=200
                )

            parsed_jobs = []
            for raw_job in data:
                job_obj = self.parse_lever_job(raw_job)
                if job_obj:
                    parsed_jobs.append(job_obj)

            return FetchResult(
                jobs=parsed_jobs,
                total_raw=len(data),
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

    def parse_lever_job(self, raw_job: dict) -> Optional[Job]:
        raw_id = str(raw_job.get("id", ""))
        if not raw_id:
            return None

        title = raw_job.get("text", "").strip()
        if not title:
            return None

        job_id = generate_job_id(self.source_name(), raw_id)

        # Lever createdAt timestamp (epoch milliseconds)
        posted_at = None
        created_at_ms = raw_job.get("createdAt")
        if isinstance(created_at_ms, (int, float)) and created_at_ms > 0:
            posted_at = datetime.fromtimestamp(created_at_ms / 1000.0, tz=timezone.utc)

        confidence = "HIGH" if posted_at is not None else "MEDIUM"
        freshness_cls = calculate_freshness_class(posted_at, None)

        source_url = raw_job.get("hostedUrl", "")
        canonical_url = build_canonical_url(source_url)

        categories = raw_job.get("categories", {})
        location = categories.get("location") if isinstance(categories, dict) else None
        employment_type = categories.get("commitment") if isinstance(categories, dict) else None

        desc_plain = raw_job.get("descriptionPlain", "")
        desc_html = raw_job.get("content", {}).get("description", "") if isinstance(raw_job.get("content"), dict) else ""
        
        description = desc_plain.strip() or clean_html(desc_html)
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
            updated_at=None,
            first_seen_at=now,
            last_seen_at=now,
            last_verified_at=now,
            freshness_confidence=confidence,
            company=company,
            title=title,
            employment_type=employment_type,
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
