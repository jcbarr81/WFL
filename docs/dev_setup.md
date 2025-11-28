# Dev Setup and Run Guide

## Prereqs
- Python 3.12+
- Node 20+ (for frontend)
- Docker & docker-compose (optional for containerized run)

## Backend (local)
1) Create env and install deps:
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```
2) Configure env (copy example):
```bash
cp .env.example .env
```
3) Run migrations:
```bash
cd backend
python manage.py migrate
```
4) (Optional) Seed sample data:
```bash
python manage.py seed_sample_league
# user: commish@example.com / password123
```
5) Start server:
```bash
python manage.py runserver
```

## Backend (docker-compose)
```bash
docker-compose up --build
```
- Backend at http://localhost:8000
- Frontend dev server at http://localhost:3000 (requires npm install inside container on first build)

## Frontend
1) Install deps:
```bash
cd frontend
npm install
```
2) Run dev server:
```bash
npm run dev -- --host 0.0.0.0 --port 3000
```

## API Smoke Tests
- Health: `GET /api/health/`
- Auth: `POST /api/auth/register/`, `POST /api/auth/login/`, `GET /api/auth/me/`, `POST /api/auth/logout/`
- League: `POST /api/leagues/` to create (scaffolds conferences/divisions), `GET /api/leagues/`, `GET /api/leagues/<id>/structure/`
- Teams: `POST /api/leagues/<league_id>/teams/create/` with conference/division IDs from structure, `GET /api/leagues/<league_id>/teams/`

## Tests
```bash
PYTHONPATH=backend .venv/bin/pytest
```
