from collector.core.models import Source
from collector.sources.score import SourceScoreEvaluator

def test_source_score_calculation_high_yield():
    source = Source(
        source_id="high_yield",
        company_name="HighCorp",
        ats_platform="greenhouse",
        board_token="high",
        base_url="http://example.com",
        relevant_jobs_30d=10,
        fresh_jobs_30d=5,
        total_jobs_fetched_30d=50,
        total_requests_30d=100,
        successful_requests_30d=98,
        failed_requests_30d=2,
    )
    score = source.calculate_score()
    # yield=100, fresh=75, rel=98, fail=2%, dup=0 -> score should be high (>85)
    assert score >= 85.0
    tier = source.evaluate_tier_promotion()
    assert tier == "P0"

def test_source_score_calculation_high_failure():
    source = Source(
        source_id="failing_corp",
        company_name="FailingCorp",
        ats_platform="lever",
        board_token="fail",
        base_url="http://example.com",
        total_requests_30d=100,
        successful_requests_30d=20,
        failed_requests_30d=80,
    )
    score = source.calculate_score()
    assert score < 20.0
    tier = source.evaluate_tier_promotion()
    assert tier in ("P2", "P3")

def test_evaluate_all_summary():
    s1 = Source(source_id="s1", company_name="C1", ats_platform="g", board_token="t1", base_url="u1", tier="P2", relevant_jobs_30d=8, fresh_jobs_30d=5, total_requests_30d=10, successful_requests_30d=10)
    s2 = Source(source_id="s2", company_name="C2", ats_platform="l", board_token="t2", base_url="u2", tier="P0", consecutive_failures=10)
    
    tier_summary = SourceScoreEvaluator.evaluate_all([s1, s2])
    assert tier_summary["P0"] == 1
    assert tier_summary["P3"] == 1
