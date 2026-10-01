import re
import hashlib
from typing import Optional
from bs4 import BeautifulSoup

JAVA_SKILLS = [
    "java", "spring", "spring boot", "hibernate", "jpa", "microservices",
    "kafka", "rabbitmq", "aws", "gcp", "azure", "docker", "kubernetes",
    "postgresql", "mysql", "mongodb", "redis", "maven", "gradle", "rest",
    "grpc", "graphql", "sql", "nosql", "junit", "mockito"
]

def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    # Lowercase, trim, strip punctuation and extra spaces
    cleaned = re.sub(r"\s+", " ", text.lower().strip())
    return cleaned

def clean_html(html_str: Optional[str]) -> str:
    if not html_str:
        return ""
    try:
        soup = BeautifulSoup(html_str, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        # Fallback regex strip tags
        text = re.sub(r"<[^>]+>", " ", html_str)
        return re.sub(r"\s+", " ", text).strip()

def extract_skills(text: Optional[str]) -> list[str]:
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for skill in JAVA_SKILLS:
        # Word boundary search for accurate matching
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(list(set(found)))

def compute_content_hash(company: str, title: str, description: Optional[str]) -> str:
    raw_content = f"{normalize_text(company)}|{normalize_text(title)}|{normalize_text(description or '')}"
    return hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
