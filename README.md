# ResumeIQ — AI Resume Screening System

> Python · FastAPI · NLP · Claude AI · SQLite · No Docker needed

## Project structure

```
resumeiq/
├── app/
│   ├── __init__.py
│   ├── main.py        ← FastAPI backend (all routes)
│   ├── database.py    ← SQLite persistence (aiosqlite)
│   └── nlp.py         ← Skill extraction utilities
├── frontend/
│   └── index.html     ← Complete UI (open directly in browser)
├── requirements.txt
├── .env.example
└── README.md
```

## Run in 4 commands

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
set ANTHROPIC_API_KEY=sk-ant-your-key-here    # Windows
# export ANTHROPIC_API_KEY=sk-ant-...         # Mac/Linux

# 4. Start the server
uvicorn app.main:app --reload --port 8000
```

## Open the frontend

Just open `frontend/index.html` in your browser — no build step, no npm, no Node.js needed.

- API: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs
- Frontend: open frontend/index.html directly

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/screen` | Screen resume (JSON) |
| POST | `/api/screen/upload` | Screen resume (file upload) |
| GET | `/api/screenings` | List all past screenings |
| GET | `/api/screenings/{id}` | Get one screening |



