import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .skill_extractor import extract_skills

def _semantic_similarity(resume_text: str, job_text: str) -> float:
    """TF-IDF text similarity baseline; replace with sentence embeddings later."""
    try:
        matrix = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform(
            [resume_text or "", job_text or ""]
        )
        return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except ValueError:
        return 0.0

def _experience_years(text: str) -> float | None:
    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|year|yrs|yr)\s+(?:of\s+)?(?:experience|exp)",
        r"(?:experience|exp)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years|year|yrs|yr)"
    ]
    matches = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, (text or "").lower()))
    try:
        return max(float(x) for x in matches) if matches else None
    except ValueError:
        return None

def analyze_match(resume_text: str, job_description: str, required_skills=None, required_experience=0):
    resume_skills = extract_skills(resume_text)
    job_skills = sorted(set(required_skills or extract_skills(job_description)))
    matched = sorted(set(resume_skills) & set(job_skills))
    missing = sorted(set(job_skills) - set(resume_skills))
    skill_coverage = len(matched) / len(job_skills) if job_skills else 0.0
    semantic = _semantic_similarity(resume_text, job_description)

    candidate_exp = _experience_years(resume_text)
    experience_score = None
    if required_experience and candidate_exp is not None:
        experience_score = min(candidate_exp / float(required_experience), 1.0)
    elif required_experience:
        experience_score = 0.0
    else:
        experience_score = 1.0

    # Transparent heuristic score, not a probability of job performance.
    score = (0.50 * skill_coverage + 0.35 * semantic + 0.15 * experience_score) * 100
    reasons = []
    if matched:
        reasons.append("Matched skills: " + ", ".join(matched))
    if missing:
        reasons.append("Skills to verify or develop: " + ", ".join(missing))
    if candidate_exp is None and required_experience:
        reasons.append("Experience duration was not confidently extracted; recruiter review needed.")
    return {
        "score": round(score, 1),
        "resume_skills": resume_skills,
        "job_skills": job_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "skill_coverage": round(skill_coverage * 100, 1),
        "semantic_similarity": round(semantic * 100, 1),
        "candidate_experience": candidate_exp,
        "required_experience": int(required_experience or 0),
        "experience_score": round(experience_score * 100, 1),
        "explanation": reasons,
        "score_note": "Heuristic relevance score for recruiter assistance only; not a probability or an automated hiring decision."
    }
