#!/bin/bash

# AltCare - Run Backend + Frontend
# This script starts all services needed for local development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup function for graceful shutdown
cleanup() {
    log_info "Shutting down services..."

    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        log_info "Backend stopped"
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        log_info "Frontend stopped"
    fi

    if [ ! -z "$CELERY_PID" ]; then
        kill $CELERY_PID 2>/dev/null || true
        log_info "Celery worker stopped"
    fi

    log_success "Cleanup complete"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

log_success "All prerequisites are installed"

# Parse command line arguments
START_CELERY=false
SKIP_FRONTEND=false
SKIP_BACKEND=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --celery)
            START_CELERY=true
            shift
            ;;
        --backend-only)
            SKIP_FRONTEND=true
            shift
            ;;
        --frontend-only)
            SKIP_BACKEND=true
            shift
            ;;
        -h|--help)
            echo "Usage: ./run.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --celery          Start Celery worker for background tasks (SMS/Email)"
            echo "  --backend-only    Only start backend services"
            echo "  --frontend-only   Only start frontend (assumes backend is running)"
            echo "  -h, --help        Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help to see available options"
            exit 1
            ;;
    esac
done

# Start Docker infrastructure
if [ "$SKIP_BACKEND" != true ]; then
    log_info "Starting Docker infrastructure (PostgreSQL, Redis, MinIO)..."
    docker compose up -d

    if [ $? -ne 0 ]; then
        log_error "Failed to start Docker services"
        exit 1
    fi

    log_success "Docker services started"

    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker exec altcare_postgres pg_isready -U altcare > /dev/null 2>&1; then
            log_success "PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "PostgreSQL failed to start"
            exit 1
        fi
        sleep 1
    done

    # Ensure application database exists (needed when postgres volume was initialized earlier)
    log_info "Ensuring application database exists (altcare_dev)..."
    DB_EXISTS=$(docker exec altcare_postgres psql -U altcare -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='altcare_dev';" 2>/dev/null || true)
    if [ "$DB_EXISTS" != "1" ]; then
        docker exec altcare_postgres psql -U altcare -d postgres -c "CREATE DATABASE altcare_dev;" > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            log_error "Failed to create database altcare_dev"
            exit 1
        fi
        log_success "Database altcare_dev created"
    else
        log_success "Database altcare_dev already exists"
    fi

    # Check and enable pgvector extension
    log_info "Ensuring pgvector extension is enabled..."
    docker exec altcare_postgres psql -U altcare -d altcare_dev -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>&1

    if [ $? -ne 0 ]; then
        log_error "Failed to create pgvector extension"
        exit 1
    fi

    log_success "pgvector extension enabled"
fi

# Setup and start backend
if [ "$SKIP_BACKEND" != true ]; then
    log_info "Setting up backend..."

    cd backend

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Force IPv4 localhost to avoid resolving to a different Postgres instance via ::1
    export DATABASE_URL="postgresql+asyncpg://altcare:altcare123@127.0.0.1:5433/altcare_dev"

    # Install/upgrade dependencies
    log_info "Installing backend dependencies..."
    pip install -q --upgrade pip
    pip install -q -e .

    # Check if .env exists
    if [ ! -f ".env" ]; then
        log_warn "Backend .env file not found. Please create it from .env.example"
        log_warn "Run: cp .env.example .env"
        exit 1
    fi

    # Run database migrations
    log_info "Running database migrations..."
    alembic upgrade head

    if [ $? -ne 0 ]; then
        log_error "Database migration failed"
        exit 1
    fi

    # Seed database (if not already done)
    log_info "Seeding database..."
    ./scripts/run_seed.sh > /dev/null 2>&1 || log_warn "Seed data may already exist"

    # Start backend server
    log_info "Starting backend server on http://localhost:8000"
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/altcare_backend.log 2>&1 &
    BACKEND_PID=$!

    # Wait for backend to be ready
    log_info "Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Backend is ready at http://localhost:8000"
            log_info "API docs available at http://localhost:8000/docs"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Backend failed to start. Check /tmp/altcare_backend.log for details"
            tail -n 20 /tmp/altcare_backend.log
            cleanup
            exit 1
        fi
        sleep 1
    done

    # Start Celery worker if requested
    if [ "$START_CELERY" = true ]; then
        log_info "Starting Celery worker for background tasks..."
        celery -A app.core.celery:celery_app worker --loglevel=info > /tmp/altcare_celery.log 2>&1 &
        CELERY_PID=$!
        log_success "Celery worker started"
    fi

    cd ..
fi

# Setup and start frontend
if [ "$SKIP_FRONTEND" != true ]; then
    log_info "Setting up frontend..."

    cd frontend

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm install
    fi

    # Check if .env.local exists
    if [ ! -f ".env.local" ]; then
        log_warn "Frontend .env.local file not found"
        log_info "Creating default .env.local..."
        echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
    fi

    # Start frontend server
    log_info "Starting frontend server on http://localhost:3000"
    npm run dev > /tmp/altcare_frontend.log 2>&1 &
    FRONTEND_PID=$!

    # Wait for frontend to be ready
    log_info "Waiting for frontend to be ready..."
    for i in {1..60}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            log_success "Frontend is ready at http://localhost:3000"
            break
        fi
        if [ $i -eq 60 ]; then
            log_error "Frontend failed to start. Check /tmp/altcare_frontend.log for details"
            tail -n 20 /tmp/altcare_frontend.log
            cleanup
            exit 1
        fi
        sleep 1
    done

    cd ..
fi

# Display status
echo ""
echo "=========================================="
log_success "AltCare Development Environment Running"
echo "=========================================="
echo ""

if [ "$SKIP_FRONTEND" != true ]; then
    echo -e "${GREEN}Frontend:${NC}  http://localhost:3000"
fi

if [ "$SKIP_BACKEND" != true ]; then
    echo -e "${GREEN}Backend:${NC}   http://localhost:8000"
    echo -e "${GREEN}API Docs:${NC}  http://localhost:8000/docs"
    echo -e "${GREEN}MinIO:${NC}     http://localhost:9001 (minioadmin/minioadmin)"
fi

if [ "$START_CELERY" = true ]; then
    echo -e "${GREEN}Celery:${NC}    Running (check /tmp/altcare_celery.log)"
fi

echo ""
echo "Logs:"
if [ "$SKIP_BACKEND" != true ]; then
    echo "  Backend:  tail -f /tmp/altcare_backend.log"
fi
if [ "$SKIP_FRONTEND" != true ]; then
    echo "  Frontend: tail -f /tmp/altcare_frontend.log"
fi
if [ "$START_CELERY" = true ]; then
    echo "  Celery:   tail -f /tmp/altcare_celery.log"
fi

echo ""
log_info "Press Ctrl+C to stop all services"
echo ""

# Keep script running and wait for signals
wait
