import re
from typing import Optional, Tuple

JAVA_PRIMARY_KEYWORDS = ["java", "spring", "spring boot", "spring security", "hibernate", "jpa", "microservices", "kafka"]
BACKEND_GENERAL_KEYWORDS = ["backend", "full stack", "software engineer", "rest", "grpc", "redis", "postgres", "mysql", "mongodb", "docker", "kubernetes", "aws"]

NEGATIVE_KEYWORDS = [
    r"\b\.net\b", r"\bc#\b", r"\basp\.net\b", r"\bphp\b", r"\blaravel\b", r"\bruby\b", r"\brails\b",
    r"\bui/ux designer\b", r"\bproduct manager\b", r"\bsalesforce\b", r"\baccountant\b"
]

def evaluate_java_relevance(title: str, description: Optional[str] = None) -> Tuple[bool, float, list[str]]:
    """
    Evaluates title and description for Java/Backend relevance.
    AI-Free deterministic rule engine.
    Returns: (is_relevant, relevance_score, matched_signals)
    """
    text = f"{title} {description or ''}".lower()
    title_lower = title.lower()

    # Check for Java primary signals
    java_matches = [kw for kw in JAVA_PRIMARY_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", text)]
    backend_matches = [kw for kw in BACKEND_GENERAL_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", text)]

    # Check for negative signals
    negative_matches = [pat for pat in NEGATIVE_KEYWORDS if re.search(pat, text)]

    # Python/Golang only without Java
    has_python_only = bool(re.search(r"\bpython\b", text)) and not java_matches
    has_csharp_only = bool(re.search(r"\bc#|\.net\b", text)) and not java_matches
    has_php_only = bool(re.search(r"\bphp\b", text)) and not java_matches

    matched_signals = java_matches + backend_matches

    # Scoring algorithm
    score = 0.0
    if java_matches:
        score += 60.0 + (len(java_matches) * 10.0)
    if "backend" in title_lower or "software engineer" in title_lower or "developer" in title_lower:
        score += 20.0
    if backend_matches:
        score += len(backend_matches) * 5.0

    # Penalties
    if has_csharp_only or has_php_only:
        score -= 50.0
    if has_python_only and not ("backend" in title_lower or "software" in title_lower):
        score -= 30.0

    score = max(0.0, min(100.0, score))

    # Relevance decision
    is_relevant = False
    if java_matches:
        is_relevant = True
    elif ("backend" in title_lower or "software engineer" in title_lower or "full stack" in title_lower) and not (has_csharp_only or has_php_only or negative_matches):
        if any(kw in text for kw in ["microservices", "rest", "sql", "aws", "docker", "kafka", "redis"]):
            is_relevant = True

    return is_relevant, score, matched_signals
