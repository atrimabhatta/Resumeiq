from databases import Database
import json
import os
from typing import Optional

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///resumeiq.db")
database = Database(DATABASE_URL)

is_postgres = DATABASE_URL.startswith("postgres")

async def init_db():
    if is_postgres:
        await database.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await database.execute("""
            CREATE TABLE IF NOT EXISTS screenings (
                id                    SERIAL PRIMARY KEY,
                user_id               INTEGER REFERENCES users(id),
                candidate_name        TEXT NOT NULL,
                resume_text           TEXT NOT NULL,
                job_description       TEXT NOT NULL,
                overall_score         INTEGER,
                match_score           INTEGER,
                skills_score          INTEGER,
                experience_score      INTEGER,
                verdict               TEXT,
                summary               TEXT,
                matched_skills        TEXT,
                missing_skills        TEXT,
                strengths             TEXT,
                improvements          TEXT,
                skill_breakdown       TEXT,
                hiring_recommendation TEXT,
                created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        await database.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await database.execute("""
            CREATE TABLE IF NOT EXISTS screenings (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id               INTEGER,
                candidate_name        TEXT NOT NULL,
                resume_text           TEXT NOT NULL,
                job_description       TEXT NOT NULL,
                overall_score         INTEGER,
                match_score           INTEGER,
                skills_score          INTEGER,
                experience_score      INTEGER,
                verdict               TEXT,
                summary               TEXT,
                matched_skills        TEXT,
                missing_skills        TEXT,
                strengths             TEXT,
                improvements          TEXT,
                skill_breakdown       TEXT,
                hiring_recommendation TEXT,
                created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        try:
            await database.execute("ALTER TABLE screenings ADD COLUMN user_id INTEGER REFERENCES users(id)")
        except Exception:
            pass


async def create_user(username: str, password_hash: str) -> Optional[int]:
    query = """
        INSERT INTO users (username, password_hash)
        VALUES (:username, :password_hash)
    """
    try:
        return await database.execute(query=query, values={"username": username, "password_hash": password_hash})
    except Exception as e:
        if "UNIQUE" in str(e).upper() or "duplicate key" in str(e).lower():
            return None
        raise e

async def get_user_by_username(username: str) -> Optional[dict]:
    query = "SELECT * FROM users WHERE username = :username"
    row = await database.fetch_one(query=query, values={"username": username})
    return dict(row) if row else None


async def save_screening(
    user_id: int,
    candidate_name: str,
    resume_text: str,
    job_description: str,
    result: dict
) -> int:
    query = """
        INSERT INTO screenings (
            user_id, candidate_name, resume_text, job_description,
            overall_score, match_score, skills_score, experience_score,
            verdict, summary, matched_skills, missing_skills,
            strengths, improvements, skill_breakdown, hiring_recommendation
        ) VALUES (
            :user_id, :candidate_name, :resume_text, :job_description,
            :overall_score, :match_score, :skills_score, :experience_score,
            :verdict, :summary, :matched_skills, :missing_skills,
            :strengths, :improvements, :skill_breakdown, :hiring_recommendation
        )
    """
    values = {
        "user_id": user_id,
        "candidate_name": candidate_name,
        "resume_text": resume_text,
        "job_description": job_description,
        "overall_score": result["overallScore"],
        "match_score": result["matchScore"],
        "skills_score": result["skillsScore"],
        "experience_score": result["experienceScore"],
        "verdict": result["verdict"],
        "summary": result["summary"],
        "matched_skills": json.dumps(result["matchedSkills"]),
        "missing_skills": json.dumps(result["missingSkills"]),
        "strengths": json.dumps(result["strengths"]),
        "improvements": json.dumps(result["improvements"]),
        "skill_breakdown": json.dumps(result["skillBreakdown"]),
        "hiring_recommendation": result["hiringRecommendation"]
    }
    return await database.execute(query=query, values=values)


async def get_all_screenings(user_id: int, limit: int = 20, offset: int = 0) -> list:
    query = """
        SELECT id, candidate_name, overall_score, match_score,
               verdict, summary, created_at
        FROM screenings
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """
    rows = await database.fetch_all(query=query, values={"user_id": user_id, "limit": limit, "offset": offset})
    return [dict(r) for r in rows]


async def get_screening_by_id(screening_id: int, user_id: int) -> Optional[dict]:
    query = "SELECT * FROM screenings WHERE id = :id AND user_id = :user_id"
    row = await database.fetch_one(query=query, values={"id": screening_id, "user_id": user_id})
    if not row:
        return None
    d = dict(row)
    for field in ["matched_skills", "missing_skills", "strengths",
                  "improvements", "skill_breakdown"]:
        if isinstance(d[field], str):
            d[field] = json.loads(d[field])
    return d
