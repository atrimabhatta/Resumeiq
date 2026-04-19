from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import json
import re
import os
import tempfile
from pdfminer.high_level import extract_text
from dotenv import load_dotenv

load_dotenv()

from .database import init_db, save_screening, get_all_screenings, get_screening_by_id, create_user, get_user_by_username, database

security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey_resumeiq_1234!")
ALGORITHM = "HS256"

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid auth token")
        return int(user_id)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid auth token")

from app.nlp import parse_resume

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await init_db()
    yield
    await database.disconnect()


app = FastAPI(
    title="ResumeIQ API",
    description="AI-powered resume screening system using NLP",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALL_SKILLS = [
    "python", "sql", "fastapi", "docker", "machine learning", "aws", "azure", 
    "java", "c++", "react", "javascript", "node.js", "git", "nlp", 
    "deep learning", "data visualization", "pandas", "numpy", "scikit-learn",
    "django", "flask", "kubernetes", "linux", "bash", "html", "css", "c#"
]

class ScreeningRequest(BaseModel):
    resume_text: str
    job_description: str
    candidate_name: Optional[str] = "Unknown"

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@app.post("/api/register", response_model=Token)
async def register(user: UserCreate):
    hashed = get_password_hash(user.password)
    user_id = await create_user(user.username, hashed)
    if not user_id:
        raise HTTPException(status_code=400, detail="Username already exists")
    token = create_access_token({"sub": str(user_id)})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
async def login(user: UserCreate):
    db_user = await get_user_by_username(user.username)
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": str(db_user["id"])})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/screen")
async def screen_resume(request: ScreeningRequest, user_id: int = Depends(get_current_user)):
    if len(request.resume_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Resume text too short (min 50 chars).")
    if len(request.job_description.strip()) < 30:
        raise HTTPException(status_code=400, detail="Job description too short (min 30 chars).")

    res_text = request.resume_text.lower()
    jd_text = request.job_description.lower()

    # Extract expected skills from JD (or use defaults if none found)
    expected_skills = [s for s in ALL_SKILLS if s in jd_text]
    if not expected_skills:
        expected_skills = ["python", "sql", "machine learning", "fastapi", "docker"]

    matched_skills = [s for s in expected_skills if s in res_text]
    missing_skills = [s for s in expected_skills if s not in res_text]

    # Calculate scores
    skills_score = int((len(matched_skills) / len(expected_skills)) * 100) if expected_skills else 0
    experience_score = 75 # Static fallback as parsing years of exp offline is complex
    match_score = skills_score
    overall_score = int((skills_score + experience_score + match_score) / 3)

    if overall_score >= 80:
        verdict = "STRONG MATCH"
        summary = "Candidate shows excellent skill overlap with the job description."
        hiring_rec = "Highly recommended for an interview."
    elif overall_score >= 60:
        verdict = "GOOD FIT"
        summary = "Candidate has many of the required skills but is missing a few."
        hiring_rec = "Recommended for technical screening."
    elif overall_score >= 40:
        verdict = "PARTIAL FIT"
        summary = "Candidate lacks several core skills required for the role."
        hiring_rec = "Consider only if other candidates are unavailable."
    else:
        verdict = "WEAK FIT"
        summary = "Candidate does not meet the basic requirements."
        hiring_rec = "Not recommended."

    skill_breakdown = [{"skill": s, "score": 100 if s in matched_skills else 0} for s in expected_skills]

    data = {
        "overallScore": overall_score,
        "matchScore": match_score,
        "skillsScore": skills_score,
        "experienceScore": experience_score,
        "verdict": verdict,
        "summary": summary,
        "matchedSkills": matched_skills,
        "missingSkills": missing_skills,
        "strengths": ["Matched key skills: " + ", ".join(matched_skills[:3])] if matched_skills else ["None identified"],
        "improvements": ["Needs to learn: " + ", ".join(missing_skills[:3])] if missing_skills else ["None identified"],
        "skillBreakdown": skill_breakdown,
        "hiringRecommendation": hiring_rec
    }

    record_id = await save_screening(
        user_id=user_id,
        candidate_name=request.candidate_name,
        resume_text=request.resume_text,
        job_description=request.job_description,
        result=data
    )

    return {
        "id": record_id,
        "candidate_name": request.candidate_name,
        "overall_score": data["overallScore"],
        "match_score": data["matchScore"],
        "skills_score": data["skillsScore"],
        "experience_score": data["experienceScore"],
        "verdict": data["verdict"],
        "summary": data["summary"],
        "matched_skills": data["matchedSkills"],
        "missing_skills": data["missingSkills"],
        "strengths": data["strengths"],
        "improvements": data["improvements"],
        "skill_breakdown": data["skillBreakdown"],
        "hiring_recommendation": data["hiringRecommendation"]
    }


@app.post("/api/parse-pdf")
async def parse_pdf(file: UploadFile = File(...), user_id: int = Depends(get_current_user)):
    filename = file.filename.lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files supported.")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name
        
    try:
        resume_text = extract_text(temp_path)
    finally:
        os.remove(temp_path)
        
    return {"text": resume_text}


@app.post("/api/screen/upload")
async def screen_resume_file(
    file: UploadFile = File(...),
    job_description: str = "",
    candidate_name: str = "Unknown",
    user_id: int = Depends(get_current_user)
):
    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name
        
        try:
            resume_text = extract_text(temp_path)
        finally:
            os.remove(temp_path)
            
    elif filename.endswith((".txt", ".md")):
        content = await file.read()
        resume_text = content.decode("utf-8")
    else:
        raise HTTPException(status_code=400, detail="Only .pdf, .txt or .md files supported.")
    return await screen_resume(ScreeningRequest(
        resume_text=resume_text,
        job_description=job_description,
        candidate_name=candidate_name
    ), user_id=user_id)


@app.get("/api/screenings")
async def list_screenings(limit: int = 20, offset: int = 0, user_id: int = Depends(get_current_user)):
    return await get_all_screenings(user_id=user_id, limit=limit, offset=offset)


@app.get("/api/screenings/{screening_id}")
async def get_screening(screening_id: int, user_id: int = Depends(get_current_user)):
    result = await get_screening_by_id(screening_id, user_id=user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Screening not found.")
    return result


@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")
