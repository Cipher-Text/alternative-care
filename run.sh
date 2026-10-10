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

# Fail early with a clear message instead of a half-started stack.
port_in_use() { lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }
for port in 8000 3000; do
  if port_in_use "$port"; then
    echo "Port $port is already in use. Stop the process using it (lsof -nP -iTCP:$port -sTCP:LISTEN) and retry."
    exit 1
  fi
done

if ! "$BACKEND_DIR/venv/bin/python" - <<'PY'
import asyncio, os, sys
from urllib.parse import urlparse

async def reachable(url, default_port):
    u = urlparse(url)
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(u.hostname, u.port or default_port), 3)
        w.close()
        return True
    except Exception:
        return False

checks = [("PostgreSQL", "DATABASE_URL", 5432), ("Redis", "REDIS_URL", 6379)]
bad = False
for name, var, port in checks:
    url = os.environ.get(var)
    if not url:
        print(f"{var} is not set in .env"); bad = True
    elif not asyncio.run(reachable(url, port)):
        print(f"Cannot reach {name} at {var} - start it and retry."); bad = True
sys.exit(1 if bad else 0)
PY
then
  exit 1
fi

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
  exec ./node_modules/.bin/next dev --hostname 0.0.0.0 --port 3000
) &
FRONTEND_PID=$!

# Stop a process and all of its descendants (uvicorn --reload and next dev both
# spawn children that would otherwise keep the ports busy after the launcher exits).
kill_tree() {
  local pid=$1 child
  for child in $(pgrep -P "$pid" 2>/dev/null); do
    kill_tree "$child"
  done
  kill "$pid" 2>/dev/null || true
}

cleanup() {
  trap - INT TERM EXIT
  kill_tree "$BACKEND_PID"
  kill_tree "$FRONTEND_PID"
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# End the launcher if either server exits, and clean up its sibling.
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
  sleep 1
done

STATUS=0
cleanup
exit "$STATUS"
