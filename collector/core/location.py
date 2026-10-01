import re
from typing import Optional, Tuple

INDIA_CITIES = {
    "bengaluru": "Bengaluru, India",
    "bangalore": "Bengaluru, India",
    "hyderabad": "Hyderabad, India",
    "secunderabad": "Hyderabad, India",
    "pune": "Pune, India",
    "mumbai": "Mumbai, India",
    "navi mumbai": "Mumbai, India",
    "thane": "Mumbai, India",
    "chennai": "Chennai, India",
    "noida": "Noida, India",
    "greater noida": "Noida, India",
    "gurgaon": "Gurugram, India",
    "gurugram": "Gurugram, India",
    "delhi": "Delhi NCR, India",
    "new delhi": "Delhi NCR, India",
    "delhi ncr": "Delhi NCR, India",
    "ahmedabad": "Ahmedabad, India",
    "gandhinagar": "Ahmedabad, India",
    "gujarat": "Gujarat, India",
    "kolkata": "Kolkata, India",
    "kochi": "Kochi, India",
    "cochin": "Kochi, India",
    "trivandrum": "Thiruvananthapuram, India",
    "thiruvananthapuram": "Thiruvananthapuram, India",
    "indore": "Indore, India",
    "jaipur": "Jaipur, India",
    "chandigarh": "Chandigarh, India",
}

def normalize_location(raw_location: Optional[str], is_remote_flag: Optional[bool] = None) -> Tuple[Optional[str], Optional[str], Optional[bool], str]:
    """
    Normalizes location string into standard Indian city / country and classifies remote mode.
    Returns: (normalized_location, country, is_remote, workplace_type)
    """
    if not raw_location:
        if is_remote_flag:
            return "Remote, India", "India", True, "REMOTE"
        return None, None, is_remote_flag, "ONSITE"

    loc_lower = raw_location.lower().strip()

    # Detect remote/hybrid signals
    is_remote = is_remote_flag or bool(re.search(r"\b(remote|work from home|wfh|anywhere)\b", loc_lower))
    is_hybrid = bool(re.search(r"\b(hybrid|flexible)\b", loc_lower))

    workplace_type = "HYBRID" if is_hybrid else ("REMOTE" if is_remote else "ONSITE")

    # Match Indian cities
    matched_cities = []
    for keyword, canonical in INDIA_CITIES.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", loc_lower):
            if canonical not in matched_cities:
                matched_cities.append(canonical)

    if matched_cities:
        primary_location = " / ".join(matched_cities)
        return primary_location, "India", is_remote, workplace_type

    if "india" in loc_lower or "in" == loc_lower or ", in" in loc_lower:
        if is_remote:
            return "Remote, India", "India", True, workplace_type
        return "India", "India", is_remote, workplace_type

    # Fallback to cleaned raw location
    country = "India" if "india" in loc_lower else None
    return raw_location.strip(), country, is_remote, workplace_type
