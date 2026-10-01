import re
from typing import Optional, Tuple

def extract_experience(text: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """
    Parses minimum and maximum years of experience required from title + description text.
    Returns: (experience_min, experience_max)
    """
    if not text:
        return None, None

    text_lower = text.lower()

    # Check fresher/entry-level keywords
    if re.search(r"\b(fresher|fresh graduate|entry level|trainee|0-1 year|0 to 1 year)\b", text_lower):
        return 0, 1

    # Pattern 1: Range like "2-5 years", "1 to 3 yrs", "0-2 yrs"
    range_match = re.search(r"\b(\d{1,2})\s*(?:-|to|\+)\s*(\d{1,2})\s*(?:years?|yrs?)\b", text_lower)
    if range_match:
        try:
            exp_min = int(range_match.group(1))
            exp_max = int(range_match.group(2))
            return exp_min, exp_max
        except ValueError:
            pass

    # Pattern 2: Plus like "3+ years", "5+ yrs"
    plus_match = re.search(r"\b(\d{1,2})\s*\+\s*(?:years?|yrs?)\b", text_lower)
    if plus_match:
        try:
            exp_min = int(plus_match.group(1))
            return exp_min, None
        except ValueError:
            pass

    # Pattern 3: Explicit min like "minimum 2 years" or "at least 3 yrs"
    min_match = re.search(r"\b(?:minimum|at least|min)\s*(\d{1,2})\s*(?:years?|yrs?)\b", text_lower)
    if min_match:
        try:
            exp_min = int(min_match.group(1))
            return exp_min, None
        except ValueError:
            pass

    return None, None

def is_experience_eligible(exp_min: Optional[int], user_max_exp: int = 5) -> bool:
    """
    Returns True if job's minimum experience is within user's target range.
    """
    if exp_min is None:
        return True
    return exp_min <= user_max_exp
