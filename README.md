# ResumeIQ — AI Resume Screening System

> Python · FastAPI · NLP · SQLite/PostgreSQL · JWT Auth · No Docker needed

## Project structure

```
resumeiq/
├── app/
│   ├── __init__.py
│   ├── main.py        ← FastAPI backend (all routes + auth)
│   ├── database.py    ← SQLite / PostgreSQL persistence
│   └── nlp.py         ← Skill extraction utilities
├── frontend/
│   └── index.html     ← Complete UI (open directly in browser)
├── requirements.txt
├── vercel.json        ← Vercel deployment config
├── .env.example
└── README.md
```

## Run locally (4 commands)

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and fill in your environment variables
copy .env.example .env         # Windows
# cp .env.example .env         # Mac/Linux

# 4. Start the server
uvicorn app.main:app --reload --port 8000
```

## Open the frontend

Just open `frontend/index.html` in your browser — no build step, no npm, no Node.js needed.

- API: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs
- Frontend: open frontend/index.html directly

## Deploy to Vercel + Neon PostgreSQL

1. Create a free database at [neon.tech](https://neon.tech)
2. Import this GitHub repo into [vercel.com](https://vercel.com)
3. Add environment variables in Vercel dashboard:
   - `DATABASE_URL` — your Neon PostgreSQL connection string
   - `SECRET_KEY` — a random secret string for JWT signing

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register a new user |
| POST | `/api/login` | Login and get JWT token |
| GET | `/health` | Health check |
| POST | `/api/screen` | Screen resume (JSON) |
| POST | `/api/parse-pdf` | Extract text from PDF |
| POST | `/api/screen/upload` | Screen resume (file upload) |
| GET | `/api/screenings` | List your past screenings |
| GET | `/api/screenings/{id}` | Get one screening |
