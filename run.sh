#!/usr/bin/env bash

# Run the local AltCare backend and frontend without Docker.
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

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

if [[ ! -x "$FRONTEND_DIR/node_modules/.bin/next" ]]; then
  echo "Frontend dependencies not found. Set them up first with:"
  echo "  cd frontend && npm install"
  exit 1
fi

# Export the root environment file once so both the backend and Next.js
# receive the same local configuration.
set +u
set -a
source "$ROOT_DIR/.env"
set +a
set -u

echo "Starting AltCare locally (no Docker)."
echo "PostgreSQL and Redis must already be running and configured in .env."
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop both servers."

(
  cd "$BACKEND_DIR"
  exec ./venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

(
  cd "$FRONTEND_DIR"
  exec ./node_modules/.bin/next dev --hostname 0.0.0.0
) &
FRONTEND_PID=$!

cleanup() {
  trap - INT TERM EXIT
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# End the launcher if either server exits, and clean up its sibling.
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
  sleep 1
done

STATUS=0
kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
wait "$BACKEND_PID" 2>/dev/null || STATUS=$?
wait "$FRONTEND_PID" 2>/dev/null || { [[ "$STATUS" -ne 0 ]] || STATUS=$?; }
exit "$STATUS"
