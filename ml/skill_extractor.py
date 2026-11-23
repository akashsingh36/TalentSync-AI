import re

# Extend this curated vocabulary for the roles relevant to your dataset.
SKILL_ALIASES = {
    "python": ["python"],
    "java": ["java"],
    "c++": ["c++", "cpp"],
    "sql": ["sql", "structured query language"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "natural language processing": ["natural language processing", "nlp"],
    "data analysis": ["data analysis", "data analytics"],
    "data science": ["data science"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "computer vision": ["computer vision", "opencv"],
    "flask": ["flask"],
    "django": ["django"],
    "fastapi": ["fastapi"],
    "html": ["html"],
    "css": ["css"],
    "javascript": ["javascript", "js"],
    "react": ["react", "react.js"],
    "node.js": ["node.js", "nodejs"],
    "mongodb": ["mongodb", "mongo db"],
    "mysql": ["mysql"],
    "postgresql": ["postgresql", "postgres"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "excel": ["excel", "microsoft excel"],
    "git": ["git"],
    "github": ["github"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "linux": ["linux"],
    "communication": ["communication"],
    "problem solving": ["problem solving", "problem-solving"],
    "project management": ["project management"],
    "statistics": ["statistics", "statistical analysis"],
    "data visualization": ["data visualization", "data visualisation"],
    "rest api": ["rest api", "restful api"],
}

def _contains_term(text: str, term: str) -> bool:
    # Word boundaries prevent e.g. "java" matching "javascript".
    escaped = re.escape(term)
    return bool(re.search(r"(?<![a-z0-9+#])" + escaped + r"(?![a-z0-9+#])", text))

def extract_skills(text: str) -> list[str]:
    normalized = (text or "").lower()
    found = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(_contains_term(normalized, alias) for alias in aliases):
            found.append(canonical)
    return sorted(set(found))
