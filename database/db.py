import os, sqlite3
from pathlib import Path
from flask import current_app, g

def get_db():
    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        department TEXT DEFAULT '',
        description TEXT NOT NULL,
        required_skills TEXT DEFAULT '',
        required_experience INTEGER DEFAULT 0,
        location TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT DEFAULT '',
        filename TEXT DEFAULT '',
        resume_text TEXT NOT NULL,
        skills TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS screening_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        score REAL NOT NULL,
        matched_skills TEXT DEFAULT '',
        missing_skills TEXT DEFAULT '',
        semantic_similarity REAL DEFAULT 0,
        skill_coverage REAL DEFAULT 0,
        experience_score REAL DEFAULT 0,
        explanation TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
        FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );
    """)
    db.commit()
