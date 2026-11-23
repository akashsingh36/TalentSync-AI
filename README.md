# TalentSync AI — Resume Screening & Job Matcher

A local, educational full-stack recruitment analytics prototype built with Flask, SQLite, scikit-learn, PyMuPDF, python-docx, Chart.js, HTML and CSS.

## Features
- PDF/DOCX resume text extraction
- Curated skill extraction
- Explainable heuristic matching: 50% skill coverage, 35% TF-IDF cosine similarity, 15% stated experience component
- Candidate profiles and screening history
- Job opening management and candidate ranking
- Skill-gap view and interview-question starter
- Live dashboard KPIs and Chart.js analytics
- SQLite persistence (no database server required)

## Run on Windows (VS Code)
1. Install Python 3.10 or newer.
2. Open this folder in VS Code.
3. Open Terminal → New Terminal.
4. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt:
   ```bat
   venv\Scripts\activate.bat
   ```
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Start the app:
   ```bash
   python app.py
   ```
7. Open http://127.0.0.1:5000

## First-time workflow
1. Open Job Openings and add a role.
2. Enter required skills as comma-separated values (for example: python, sql, pandas).
3. Open Resume Screening and upload a PDF or DOCX.
4. Open the candidate profile to inspect the score explanation and skill gap.
5. Open Job Matching and select the role to see ranked screening results.
6. View dashboard and analytics pages.

## Scoring explanation
- Skill coverage: detected resume skills that appear in the required skill list.
- Text similarity: TF-IDF cosine similarity between resume text and job description.
- Experience component: compares explicitly stated years of experience with the job's requested years. If no experience is required, this component is treated as satisfied; if required experience cannot be extracted, it is scored as zero and flagged for manual review.
- Overall score = 50% skill coverage + 35% text similarity + 15% experience component.

This is a heuristic relevance score, NOT a probability that a candidate will perform well. It is not a validated hiring model and must not make autonomous hiring decisions. Recruiters should review original resumes and validate extracted data. The system intentionally does not infer or use protected characteristics such as gender, caste, religion, age, disability or photographs.

## Limitations and next improvements
- Scanned/image-only PDFs require OCR; this version detects very low extracted text and asks for review.
- Skill extraction uses a curated dictionary; add synonyms, context checks and domain-specific skills.
- TF-IDF is a baseline, not a true transformer embedding model. A next phase can add Sentence Transformers (e.g. `all-MiniLM-L6-v2`) with an optional local model download.
- Add login, role-based authorization, CSRF protection, retention/deletion controls, audit logging, malware scanning and production WSGI deployment before exposing this app to real users.
- For a real deployment, configure HTTPS, a strong SECRET_KEY, secure storage and a production database.

## Project structure
```text
TalentSync-AI/
├── app.py
├── requirements.txt
├── database/
├── ml/
├── templates/
└── static/css/
```


## Interactive 3D command-center dashboard
- Three.js animated 3D neural sphere (CDN/internet required for WebGL visual)
- CSS 3D hover tilt on KPI cards and animated metric counters
- Interactive Chart.js charts, activity search and CSV export
- Dark/light theme toggle remembered in browser
- Responsive layout and reduced-motion support

The dashboard charts and KPIs are populated from SQLite. The 3D sphere is decorative; it is not a trained model or live AI inference.
