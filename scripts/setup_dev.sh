#!/usr/bin/env bash
set -euo pipefail

# Setup helper for local dev. Idempotent.
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

# Copy env template if missing
if [ ! -f .env ]; then
  cp .env.example .env
fi

cd backend
python manage.py migrate

# Seed sample data (safe to re-run)
python manage.py seed_sample_league || true

cd "$ROOT_DIR"

cat <<'MSG'

Backend ready.
- Activate env: source .venv/bin/activate
- Run server: cd backend && python manage.py runserver
- Frontend: cd frontend && npm install && npm run dev -- --host 0.0.0.0 --port 3000
MSG
