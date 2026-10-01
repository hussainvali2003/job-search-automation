import pytest
from collector.core.filtering import evaluate_java_relevance
from collector.core.experience import extract_experience, is_experience_eligible
from collector.core.location import normalize_location
from collector.sources.health import HealthTracker
from collector.core.models import Source

def test_java_relevance_evaluation():
    # 1. Direct Java title + description
    is_rel, score, signals = evaluate_java_relevance("Backend Developer", "Building Microservices with Java 21, Spring Boot, and Kafka")
    assert is_rel is True
    assert score >= 70.0
    assert "java" in signals and "spring boot" in signals

    # 2. General title with Java stack
    is_rel, score, _ = evaluate_java_relevance("Software Engineer", "Backend microservices architecture with Spring, REST, and AWS")
    assert is_rel is True

    # 3. Disqualified .NET-only title
    is_rel, score, _ = evaluate_java_relevance(".NET Core Architect", "C# ASP.NET Core Web APIs")
    assert is_rel is False
    assert score < 50.0

    # 4. Disqualified PHP-only role
    is_rel, score, _ = evaluate_java_relevance("PHP Laravel Backend Developer", "Building web applications with PHP and MySQL")
    assert is_rel is False

def test_experience_extraction():
    exp_min, exp_max = extract_experience("Senior Java Engineer (3-5 years experience)")
    assert exp_min == 3
    assert exp_max == 5

    exp_min, exp_max = extract_experience("Java Developer - 2+ yrs exp")
    assert exp_min == 2
    assert exp_max is None

    exp_min, exp_max = extract_experience("Graduate Trainee / Fresher Role")
    assert exp_min == 0
    assert exp_max == 1

    assert is_experience_eligible(2, user_max_exp=5) is True
    assert is_experience_eligible(7, user_max_exp=5) is False

def test_location_normalization():
    loc, country, remote, workplace = normalize_location("Bangalore / Bengaluru, Karnataka", is_remote_flag=False)
    assert "Bengaluru, India" in loc
    assert country == "India"
    assert workplace == "ONSITE"

    loc, country, remote, workplace = normalize_location("Gurgaon", is_remote_flag=True)
    assert "Gurugram, India" in loc
    assert remote is True
    assert workplace == "REMOTE"

    loc, country, remote, workplace = normalize_location("Hyderabad, India", is_remote_flag=False)
    assert "Hyderabad, India" in loc

def test_health_semantics():
    s = Source(source_id="h_test", company_name="TestCorp", ats_platform="greenhouse", board_token="test", base_url="")
    assert s.health_status == "OK"

    # Single failure -> ERROR
    HealthTracker.record_failure(s, duration_ms=150.0, error_msg="HTTP 404")
    assert s.health_status == "ERROR"

    # 3 failures -> WARN
    HealthTracker.record_failure(s, duration_ms=150.0, error_msg="HTTP 404")
    HealthTracker.record_failure(s, duration_ms=150.0, error_msg="HTTP 404")
    assert s.health_status == "WARN"

    # Recovery -> OK
    HealthTracker.record_success(s, duration_ms=100.0, jobs_count=5, relevant_count=3, fresh_count=2)
    assert s.health_status == "OK"
