from datetime import datetime, timezone
from collector.core.models import Source

class HealthTracker:
    @staticmethod
    def record_success(source: Source, duration_ms: float, jobs_count: int, relevant_count: int, fresh_count: int) -> None:
        now = datetime.now(timezone.utc)
        source.last_fetched_at = now
        source.last_success_at = now
        source.consecutive_failures = 0
        
        source.total_requests_30d += 1
        source.successful_requests_30d += 1
        source.total_jobs_fetched_30d += jobs_count
        source.relevant_jobs_30d += relevant_count
        source.fresh_jobs_30d += fresh_count
        
        # Exponential moving average for response time
        if source.avg_response_time_ms == 0.0:
            source.avg_response_time_ms = duration_ms
        else:
            source.avg_response_time_ms = (0.8 * source.avg_response_time_ms) + (0.2 * duration_ms)
            
        # Recovery towards OK
        if source.health_status in ["ERROR", "WARN", "SUSPECTED_BROKEN"]:
            source.health_status = "OK"

    @staticmethod
    def record_failure(source: Source, duration_ms: float, error_msg: str) -> None:
        now = datetime.now(timezone.utc)
        source.last_fetched_at = now
        source.consecutive_failures += 1
        source.total_requests_30d += 1
        source.failed_requests_30d += 1

        if source.consecutive_failures >= 10:
            source.health_status = "SUSPECTED_BROKEN"
            source.tier = "P3"
        elif source.consecutive_failures >= 3:
            source.health_status = "WARN"
            source.tier = "P2"
        else:
            source.health_status = "ERROR"
