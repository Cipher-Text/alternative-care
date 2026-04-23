#!/bin/bash
# Quick script to run database seeding

set -e

echo "🌱 AltCare Database Seeding Script"
echo "=================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "   Please start Docker Desktop and try again."
    exit 1
fi

# Check if database container is running
if ! docker compose ps postgres | grep -q "running"; then
    echo "⚠️  Database container is not running."
    echo "   Starting Docker services..."
    docker compose up -d postgres redis minio
    echo "   Waiting for database to be ready..."
    sleep 5
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: python3 -m venv venv && source venv/bin/activate && pip install -e ."
    exit 1
fi

# Activate virtual environment and run seed
echo "✅ Running seed script..."
echo ""
source venv/bin/activate
python scripts/seed.py

echo ""
echo "✅ Done! You can now use the seeded data."
echo ""
echo "📝 Quick login test:"
echo "   curl -X POST http://localhost:8000/api/v1/auth/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\": \"dr.rahman@example.com\", \"password\": \"Test@1234\"}'"
