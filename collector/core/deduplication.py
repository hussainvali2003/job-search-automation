import hashlib
from typing import Optional
from collector.core.models import Job
from collector.core.database import Database
from collector.core.state import StateManager

class DeduplicationEngine:
    @staticmethod
    def process_job(job: Job, db: Database, state_mgr: StateManager) -> tuple[Job, bool]:
        """
        Processes job through deduplication and repost detection:
        1. Checks database/state for exact ID occurrence.
        2. Performs cross-source matching (Company + Title + Location / Content Hash).
        3. Performs repost detection (same company + title reappeared with new ID).
        4. Preserves original first_seen_at.
        Returns: (processed_job, is_content_changed)
        """
        existing_job = db.get_job_by_id(job.id)
        is_content_changed = False

        if existing_job:
            job.first_seen_at = existing_job.first_seen_at
            job.is_new = False
            job.duplicate_group_id = existing_job.duplicate_group_id or existing_job.id
            if existing_job.content_hash and job.content_hash and job.content_hash != existing_job.content_hash:
                is_content_changed = True
            return job, is_content_changed

        # Check if ID was seen in state branch
        if not state_mgr.is_new(job.id):
            job.is_new = False

        # Cross-Source & Repost Query in DB by company_normalized
        similar_jobs = db.get_jobs_by_company(job.company_normalized) if hasattr(db, "get_jobs_by_company") else []

        match_found = None
        for s_job in similar_jobs:
            if s_job.id == job.id:
                continue

            # Title matching (exact or high substring match)
            same_title = (job.title_normalized == s_job.title_normalized) or (
                len(job.title_normalized) > 5 and job.title_normalized in s_job.title_normalized
            )

            # Location matching (overlapping or both remote or same city)
            loc1 = (job.location or "").lower()
            loc2 = (s_job.location or "").lower()
            same_loc = (loc1 == loc2) or (job.remote and s_job.remote) or ("india" in loc1 and "india" in loc2)

            # Content hash matching
            same_content = bool(job.content_hash and s_job.content_hash and job.content_hash == s_job.content_hash)

            if same_title and (same_loc or same_content):
                match_found = s_job
                break

        if match_found:
            group_id = match_found.duplicate_group_id or match_found.id
            job.duplicate_group_id = group_id
            job.first_seen_at = match_found.first_seen_at
            job.is_new = False

            if match_found.source == job.source:
                # Same source, new source_job_id -> Repost
                job.is_repost = True
            else:
                # Different source -> Cross-source duplicate
                job.is_repost = False
        else:
            if job.is_new:
                state_mgr.mark_seen([job.id])
            group_key = f"{job.company_normalized}|{job.title_normalized}|{job.content_hash[:10] if job.content_hash else ''}"
            job.duplicate_group_id = hashlib.md5(group_key.encode("utf-8")).hexdigest()[:12]

        return job, is_content_changed
