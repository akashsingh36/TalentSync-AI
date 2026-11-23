import os, json, re
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from dotenv import load_dotenv
from database.db import get_db, close_db, init_db
from ml.resume_parser import extract_resume_text
from ml.skill_extractor import extract_skills
from ml.matcher import analyze_match

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-this-secret"),
    DATABASE_PATH=os.getenv("DATABASE_PATH", str(BASE_DIR / "talentsync.db")),
    UPLOAD_FOLDER=str(BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")),
    MAX_CONTENT_LENGTH=int(os.getenv("MAX_CONTENT_LENGTH_MB", "8")) * 1024 * 1024,
)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
app.teardown_appcontext(close_db)

with app.app_context():
    init_db()

ALLOWED_EXTENSIONS = {"pdf", "docx"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_csv(value):
    return [x.strip().lower() for x in (value or "").split(",") if x.strip()]

@app.errorhandler(RequestEntityTooLarge)
def too_large(_error):
    flash("File is too large. Maximum upload size is 8 MB.", "error")
    return redirect(request.referrer or url_for("screening"))

@app.route("/")
def dashboard():
    db = get_db()
    metrics = {
        "jobs": db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
        "candidates": db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0],
        "screenings": db.execute("SELECT COUNT(*) FROM screening_results").fetchone()[0],
        "shortlisted": db.execute("SELECT COUNT(*) FROM screening_results WHERE score >= 70").fetchone()[0],
    }
    avg = db.execute("SELECT AVG(score) FROM screening_results").fetchone()[0]
    metrics["average"] = round(avg or 0, 1)
    recent = db.execute("""
        SELECT sr.id, c.name, j.title, sr.score, sr.created_at
        FROM screening_results sr
        JOIN candidates c ON c.id=sr.candidate_id
        JOIN jobs j ON j.id=sr.job_id
        ORDER BY sr.created_at DESC LIMIT 8
    """).fetchall()
    job_counts = db.execute("""
        SELECT j.title, COUNT(sr.id) AS total
        FROM jobs j LEFT JOIN screening_results sr ON sr.job_id=j.id
        GROUP BY j.id ORDER BY total DESC LIMIT 6
    """).fetchall()
    score_counts = db.execute("""
        SELECT
          SUM(CASE WHEN score >= 70 THEN 1 ELSE 0 END) AS strong,
          SUM(CASE WHEN score >= 40 AND score < 70 THEN 1 ELSE 0 END) AS review,
          SUM(CASE WHEN score < 40 THEN 1 ELSE 0 END) AS low
        FROM screening_results
    """).fetchone()
    return render_template("dashboard.html", metrics=metrics, recent=recent,
                           job_counts=[dict(x) for x in job_counts],
                           score_counts=[score_counts["strong"] or 0, score_counts["review"] or 0, score_counts["low"] or 0])

@app.route("/jobs", methods=["GET", "POST"])
def jobs():
    db = get_db()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title or not description:
            flash("Job title and description are required.", "error")
        else:
            db.execute("""INSERT INTO jobs(title, department, description, required_skills, required_experience, location)
                VALUES(?,?,?,?,?,?)""",
                (title, request.form.get("department","").strip(), description,
                 ", ".join(parse_csv(request.form.get("required_skills",""))),
                 max(0, int(request.form.get("required_experience") or 0)),
                 request.form.get("location","").strip()))
            db.commit()
            flash("Job opening created.", "success")
            return redirect(url_for("jobs"))
    rows = db.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    return render_template("jobs.html", jobs=rows)

@app.route("/screening", methods=["GET", "POST"])
def screening():
    db = get_db()
    job_rows = db.execute("SELECT * FROM jobs ORDER BY title").fetchall()
    if request.method == "POST":
        file = request.files.get("resume")
        job_id = request.form.get("job_id", type=int)
        name = request.form.get("candidate_name", "").strip()
        email = request.form.get("candidate_email", "").strip()
        if not file or not file.filename or not allowed_file(file.filename):
            flash("Choose a PDF or DOCX resume.", "error")
            return redirect(url_for("screening"))
        if not name or not job_id:
            flash("Candidate name and a job opening are required.", "error")
            return redirect(url_for("screening"))
        job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not job:
            flash("Selected job was not found.", "error")
            return redirect(url_for("screening"))
        safe_original = secure_filename(file.filename)
        # Random server-side filename avoids collisions and path traversal.
        import uuid
        stored_name = uuid.uuid4().hex + "_" + safe_original
        path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
        try:
            file.save(path)
            text = extract_resume_text(path)
            if len(text.strip()) < 30:
                raise ValueError("Very little text was extracted. Scanned image-only PDFs need OCR.")
            required = parse_csv(job["required_skills"]) or extract_skills(job["description"])
            result = analyze_match(text, job["description"], required, job["required_experience"])
            cur = db.execute("INSERT INTO candidates(name,email,filename,resume_text,skills) VALUES(?,?,?,?,?)",
                              (name, email, safe_original, text, ", ".join(result["resume_skills"])))
            candidate_id = cur.lastrowid
            db.execute("""INSERT INTO screening_results(candidate_id,job_id,score,matched_skills,missing_skills,
                       semantic_similarity,skill_coverage,experience_score,explanation)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                       (candidate_id, job_id, result["score"], ", ".join(result["matched_skills"]),
                        ", ".join(result["missing_skills"]), result["semantic_similarity"],
                        result["skill_coverage"], result["experience_score"],
                        json.dumps(result["explanation"])))
            db.commit()
            flash(f"Resume analyzed. Match score: {result['score']}%. Recruiter review is required.", "success")
            return redirect(url_for("candidate_detail", candidate_id=candidate_id))
        except Exception as exc:
            flash(f"Could not analyze resume: {exc}", "error")
        finally:
            if os.path.exists(path):
                os.remove(path)
    return render_template("screening.html", jobs=job_rows)

@app.route("/candidates")
def candidates():
    rows = get_db().execute("""
      SELECT c.id,c.name,c.email,c.skills,c.created_at,
             MAX(sr.score) AS best_score, COUNT(sr.id) AS total_screenings
      FROM candidates c LEFT JOIN screening_results sr ON sr.candidate_id=c.id
      GROUP BY c.id ORDER BY c.created_at DESC
    """).fetchall()
    return render_template("candidates.html", candidates=rows)

@app.route("/candidate/<int:candidate_id>")
def candidate_detail(candidate_id):
    db = get_db()
    candidate = db.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)).fetchone()
    if not candidate:
        flash("Candidate not found.", "error")
        return redirect(url_for("candidates"))
    results = db.execute("""
      SELECT sr.*, j.title AS job_title, j.required_skills, j.required_experience
      FROM screening_results sr JOIN jobs j ON j.id=sr.job_id
      WHERE sr.candidate_id=? ORDER BY sr.created_at DESC
    """, (candidate_id,)).fetchall()
    return render_template("candidate_detail.html", candidate=candidate, results=results)

@app.route("/matching")
def matching():
    db = get_db()
    job_id = request.args.get("job_id", type=int)
    jobs = db.execute("SELECT * FROM jobs ORDER BY title").fetchall()
    selected = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone() if job_id else None
    rows = []
    if selected:
        rows = db.execute("""
          SELECT c.id,c.name,c.email,c.skills,sr.score,sr.matched_skills,sr.missing_skills,
                 sr.skill_coverage,sr.semantic_similarity,sr.experience_score,sr.created_at
          FROM screening_results sr JOIN candidates c ON c.id=sr.candidate_id
          WHERE sr.job_id=? ORDER BY sr.score DESC
        """, (job_id,)).fetchall()
    return render_template("matching.html", jobs=jobs, selected=selected, results=rows)

@app.route("/analytics")
def analytics():
    db = get_db()
    monthly = db.execute("""
      SELECT strftime('%Y-%m', created_at) AS month, COUNT(*) AS total,
             ROUND(AVG(score),1) AS avg_score
      FROM screening_results GROUP BY month ORDER BY month DESC LIMIT 8
    """).fetchall()
    skills = db.execute("SELECT skills FROM candidates").fetchall()
    from collections import Counter
    counts = Counter()
    for row in skills:
        counts.update(parse_csv(row["skills"]))
    top_skills = counts.most_common(10)
    return render_template("analytics.html", monthly=[dict(x) for x in reversed(monthly)],
                           top_skills=top_skills)

@app.route("/skill-gap/<int:candidate_id>/<int:job_id>")
def skill_gap(candidate_id, job_id):
    db = get_db()
    row = db.execute("""
      SELECT c.name,c.skills,sr.matched_skills,sr.missing_skills,sr.score,j.title
      FROM candidates c JOIN screening_results sr ON sr.candidate_id=c.id
      JOIN jobs j ON j.id=sr.job_id
      WHERE c.id=? AND j.id=? ORDER BY sr.created_at DESC LIMIT 1
    """, (candidate_id, job_id)).fetchone()
    if not row:
        flash("No matching analysis found.", "error")
        return redirect(url_for("candidates"))
    return render_template("skill_gap.html", result=row)

@app.route("/api/interview-questions", methods=["POST"])
def interview_questions():
    data = request.get_json(silent=True) or {}
    skills = data.get("skills", [])
    if not isinstance(skills, list):
        return jsonify({"error":"skills must be a list"}), 400
    questions = []
    for skill in skills[:8]:
        s = str(skill)[:60]
        questions.extend([
            f"Explain a project where you used {s}. What was your contribution?",
            f"What common challenges arise when using {s}, and how would you solve one?",
        ])
    return jsonify({"questions": questions[:12],
                    "note":"Question prompts are generated from detected skills. They are not an assessment of candidate ability."})

@app.route("/health")
def health():
    return jsonify({"status":"ok","application":"TalentSync AI"})

if __name__ == "__main__":
    app.run(debug=True)
