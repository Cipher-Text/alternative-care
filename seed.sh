#!/usr/bin/env bash

# Load the local AltCare seed data without starting the app.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  echo "Root .env not found. Create it from the example first:"
  echo "  cp .env.example .env"
  exit 1
fi

if [[ ! -x "$BACKEND_DIR/venv/bin/python" ]]; then
  echo "Backend environment not found. Set it up first with:"
  echo "  cd backend && python3 -m venv venv && venv/bin/pip install -e ."
  exit 1
fi

# Seed script reads the database configuration from the root .env.
set +u
set -a
source "$ROOT_DIR/.env"
set +a
set -u

echo "Applying database migrations..."
cd "$BACKEND_DIR"
./venv/bin/python -m alembic upgrade head

echo "Loading database seed data..."
exec ./venv/bin/python scripts/seed.py
