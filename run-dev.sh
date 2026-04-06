#!/usr/bin/env bash
# Install dependencies and run Backend + frontend together.
# Backend: http://localhost:3000 (or PORT env)
# Frontend (Vite): http://localhost:5173 — API proxied via /api (needs MongoDB).
# Start MongoDB first, e.g.: docker compose up mongo -d

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "Installing Backend dependencies..."
(cd Backend && npm install)

echo "Installing frontend dependencies..."
(cd frontend && npm install)

echo "Starting Backend (npm start) and frontend (npm run dev). Press Ctrl+C to stop both."
(cd Backend && npm start) &
BACKEND_PID=$!
(cd frontend && npm run dev) &
FRONTEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM

wait "$BACKEND_PID" "$FRONTEND_PID"
