from pathlib import Path
import fitz
from docx import Document

def extract_resume_text(path: str) -> str:
    """Extract text from a PDF or DOCX resume."""
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        chunks = []
        with fitz.open(path) as pdf:
            for page in pdf:
                chunks.append(page.get_text("text"))
        return "\n".join(chunks).strip()
    if suffix == ".docx":
        doc = Document(path)
        chunks = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                chunks.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(chunks).strip()
    raise ValueError("Only PDF and DOCX files are supported.")
