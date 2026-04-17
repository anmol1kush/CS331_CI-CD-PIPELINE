#!/usr/bin/env bash
# Start development environment: MongoDB, Backend + Frontend with one command
# Backend: http://localhost:8000
# Frontend (Vite): http://localhost:5173 — API proxied via /api
# MongoDB: mongodb://localhost:27017/cicd_app

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log() {
  echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if MongoDB is running
check_mongodb() {
  # Try to verify MongoDB is already running using mongosh/mongo CLI
  if mongosh --eval "db.adminCommand('ping')" --quiet 2>/dev/null; then
    success "MongoDB is running"
    return 0
  fi
  
  if mongo --eval "db.adminCommand('ping')" --quiet 2>/dev/null; then
    success "MongoDB is running"
    return 0
  fi
  
  log "MongoDB not running. Checking for Docker..."
  if ! command -v docker &> /dev/null; then
    error "Docker not found. Please start MongoDB manually:"
    error "  Option 1: docker compose up mongo -d"
    error "  Option 2: Start MongoDB service directly"
    return 1
  fi
  
  log "Starting MongoDB via Docker..."
  # Try with docker compose (with or without sudo)
  local docker_cmd="docker"
  if ! docker ps > /dev/null 2>&1; then
    log "Docker requires sudo, attempting with sudo..."
    docker_cmd="sudo docker"
  fi
  
  if $docker_cmd compose up mongo -d 2>/dev/null; then
    log "MongoDB container started, waiting for it to be ready..."
    sleep 5
    
    # Verify MongoDB container is actually running
    if $docker_cmd ps | grep -q "mongo.*27017"; then
      log "MongoDB container is running on port 27017"
      
      # Try to ping with mongosh/mongo if available
      if mongosh --eval "db.adminCommand('ping')" --quiet 2>/dev/null || mongo --eval "db.adminCommand('ping')" --quiet 2>/dev/null; then
        success "MongoDB is responding to connections"
      else
        # Container is running but can't connect via CLI tools
        # This is usually because mongosh/mongo CLI is not installed locally
        # But MongoDB is running in container, so proceed anyway
        log "MongoDB CLI tools not available locally, but container is running"
        log "Backend will connect to MongoDB via connection string"
      fi
      
      success "MongoDB started and ready"
      return 0
    else
      error "MongoDB container failed to start"
      error "Trying to see logs..."
      $docker_cmd compose logs mongo 2>/dev/null | tail -10 || true
      return 1
    fi
  else
    error "Failed to execute: $docker_cmd compose up mongo -d"
    error "Troubleshooting:"
    error "  1. Make sure docker-compose.yml exists in current directory"
    error "  2. Fix Docker permissions: sudo usermod -aG docker \$USER"
    error "  3. Test Docker: $docker_cmd ps"
    return 1
  fi
}

# Wait for backend to be ready
wait_for_backend() {
  local max_attempts=30
  local attempt=1
  
  log "Waiting for backend to be ready (http://localhost:8000)..."
  while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
      success "Backend is ready!"
      return 0
    fi
    echo -n "."
    sleep 1
    ((attempt++))
  done
  
  error "Backend failed to start"
  return 1
}

cleanup() {
  log "Shutting down services..."
  
  # Only kill processes if they were started
  if [ ! -z "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  
  if [ ! -z "${FRONTEND_PID:-}" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  
  wait 2>/dev/null || true
  success "All services stopped"
}

# Set up trap for cleanup
trap cleanup INT TERM EXIT

# Check MongoDB
log "Checking MongoDB..."
check_mongodb || exit 1

log "Installing Backend dependencies..."
(cd Backend && npm install > /dev/null 2>&1) &
BACKEND_INSTALL_PID=$!

log "Installing frontend dependencies..."
(cd frontend && npm install > /dev/null 2>&1) &
FRONTEND_INSTALL_PID=$!

wait $BACKEND_INSTALL_PID $FRONTEND_INSTALL_PID
success "Dependencies installed"

log "Starting Backend on port 8000..."
export PORT=8000
(cd Backend && npm start) &
BACKEND_PID=$!

# Wait for backend to be ready
wait_for_backend || {
  kill $BACKEND_PID 2>/dev/null || true
  exit 1
}

log "Starting Frontend on port 5173..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

success "All services started!"
echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  📱 Frontend: http://localhost:5173${NC}"
echo -e "${GREEN}  🔧 Backend:  http://localhost:8000${NC}"
echo -e "${GREEN}  🗄️  MongoDB:  mongodb://localhost:27017${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
log "Press Ctrl+C to stop all services"
echo ""

wait "$BACKEND_PID" "$FRONTEND_PID"

