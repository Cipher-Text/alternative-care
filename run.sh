#!/usr/bin/env sh

# Start the complete AltCare development stack through Docker Compose.
set -eu
cd "$(dirname "$0")"
exec docker compose up --build "$@"
