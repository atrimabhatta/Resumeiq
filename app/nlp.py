import re
from typing import Optional

SKILL_PATTERNS = {
    "languages":  r"\b(python|java|javascript|typescript|go|rust|c\+\+|sql|r\b|scala|kotlin|swift)\b",
    "ml_ai":      r"\b(machine learning|deep learning|nlp|natural language processing|computer vision|tensorflow|pytorch|scikit.learn|huggingface|transformers|llm|generative ai|bert|gpt|xgboost|random forest|neural network)\b",
    "data":       r"\b(pandas|numpy|matplotlib|seaborn|plotly|power bi|tableau|dax|excel|spark|hadoop|airflow|dbt|etl|data pipeline)\b",
    "cloud":      r"\b(aws|azure|gcp|google cloud|docker|kubernetes|terraform|ci/cd|github actions|jenkins|heroku|vercel|railway)\b",
    "databases":  r"\b(postgresql|mysql|mongodb|redis|elasticsearch|sqlite|dynamodb|firebase|supabase)\b",
    "web":        r"\b(fastapi|django|flask|react|vue|next\.?js|node|express|rest api|graphql|html|css)\b",
    "tools":      r"\b(git|github|linux|bash|agile|scrum|jira|postman|jupyter)\b",
    "security":   r"\b(cissp|cybersecurity|penetration testing|owasp|encryption|ssl|tls|oauth|jwt)\b",
}

EDUCATION_PATTERNS = {
    "phd":       r"\b(ph\.?d|doctorate|doctoral)\b",
    "masters":   r"\b(m\.?s\.?|m\.?e\.?|m\.?tech|mca|master[s]?|msc)\b",
    "bachelors": r"\b(b\.?e\.?|b\.?tech|b\.?sc|bca|bachelor[s]?|b\.?s\.?)\b",
}

EXPERIENCE_RE = re.compile(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)", re.I)
EMAIL_RE      = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I)
GITHUB_RE     = re.compile(r"github\.com/[\w\-]+", re.I)
LINKEDIN_RE   = re.compile(r"linkedin\.com/in/[\w\-]+", re.I)


def extract_skills(text: str) -> dict:
    text_lower = text.lower()
    result = {}
    for category, pattern in SKILL_PATTERNS.items():
        found = list(set(re.findall(pattern, text_lower, re.I)))
        if found:
            result[category] = sorted(found)
    return result


def extract_education_level(text: str) -> str:
    text_lower = text.lower()
    for level, pattern in EDUCATION_PATTERNS.items():
        if re.search(pattern, text_lower):
            return level
    return "unknown"


def extract_contact_info(text: str) -> dict:
    return {
        "email":    m.group() if (m := EMAIL_RE.search(text)) else None,
        "github":   m.group() if (m := GITHUB_RE.search(text)) else None,
        "linkedin": m.group() if (m := LINKEDIN_RE.search(text)) else None,
    }


def parse_resume(text: str) -> dict:
    return {
        "word_count":      len(text.split()),
        "skills":          extract_skills(text),
        "experience_years": int(m.group(1)) if (m := EXPERIENCE_RE.search(text)) else None,
        "education_level": extract_education_level(text),
        "contact":         extract_contact_info(text),
    }
