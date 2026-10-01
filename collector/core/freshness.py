from datetime import datetime, timezone
from typing import Optional, Any
from collections import Counter

FRESHNESS_CLASSES = ["<6h", "<12h", "<24h", "24-48h", "48-72h", "3-7d", ">7d", "UNKNOWN"]

def calculate_freshness_class(
    posted_at: Optional[datetime],
    updated_at: Optional[datetime],
    ref_time: Optional[datetime] = None
) -> str:
    """
    Computes freshness class based strictly on employer timestamps (posted_at or updated_at).
    Does NOT use fetched_at / discovery time as publication date.
    Returns: '<6h', '<12h', '<24h', '24-48h', '48-72h', '3-7d', '>7d', or 'UNKNOWN'
    """
    ts = posted_at or updated_at
    if ts is None:
        return "UNKNOWN"

    now = ref_time or datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    age_hours = (now - ts).total_seconds() / 3600.0

    if age_hours <= 6.0:
        return "<6h"
    elif age_hours <= 12.0:
        return "<12h"
    elif age_hours <= 24.0:
        return "<24h"
    elif age_hours <= 48.0:
        return "24-48h"
    elif age_hours <= 72.0:
        return "48-72h"
    elif age_hours <= 168.0:
        return "3-7d"
    else:
        return ">7d"

def compute_freshness_metrics(jobs: list[Any]) -> dict[str, Any]:
    """Computes comprehensive freshness quality metrics across collected jobs."""
    total_jobs = len(jobs)
    if total_jobs == 0:
        return {
            "total_jobs": 0, "jobs_under_24h": 0, "jobs_under_48h": 0, "jobs_under_72h": 0,
            "jobs_over_7d": 0, "jobs_with_trustworthy_posted_at": 0, "jobs_with_only_first_seen_at": 0,
            "freshness_class_distribution": {}, "freshness_confidence_distribution": {}
        }

    fc_dist = Counter(getattr(j, "freshness_class", "UNKNOWN") for j in jobs)
    conf_dist = Counter(getattr(j, "freshness_confidence", "UNKNOWN") for j in jobs)

    jobs_under_24h = fc_dist["<6h"] + fc_dist["<12h"] + fc_dist["<24h"]
    jobs_under_48h = jobs_under_24h + fc_dist["24-48h"]
    jobs_under_72h = jobs_under_48h + fc_dist["48-72h"]
    jobs_over_7d = fc_dist[">7d"]

    trustworthy_count = sum(1 for j in jobs if getattr(j, "posted_at", None) is not None)
    only_first_seen_count = sum(1 for j in jobs if getattr(j, "posted_at", None) is None and getattr(j, "updated_at", None) is None)

    return {
        "total_jobs": total_jobs,
        "jobs_under_24h": jobs_under_24h,
        "jobs_under_48h": jobs_under_48h,
        "jobs_under_72h": jobs_under_72h,
        "jobs_over_7d": jobs_over_7d,
        "jobs_with_trustworthy_posted_at": trustworthy_count,
        "jobs_with_only_first_seen_at": only_first_seen_count,
        "freshness_class_distribution": dict(fc_dist),
        "freshness_confidence_distribution": dict(conf_dist)
    }
