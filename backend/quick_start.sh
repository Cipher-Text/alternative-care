#!/bin/bash

# AltCare Backend Quick Start Script
# Run this script to set up the backend development environment

set -e

echo "🚀 AltCare Backend Quick Start"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Step 1: Start infrastructure services
echo "📦 Step 1: Starting infrastructure services..."
docker compose up -d postgres redis minio

echo "⏳ Waiting for services to be ready (15 seconds)..."
sleep 15

# Verify services
if docker compose ps | grep -q "postgres.*running"; then
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
else
    echo -e "${RED}❌ PostgreSQL failed to start${NC}"
    exit 1
fi

if docker compose ps | grep -q "redis.*running"; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis failed to start${NC}"
    exit 1
fi

if docker compose ps | grep -q "minio.*running"; then
    echo -e "${GREEN}✅ MinIO is running${NC}"
else
    echo -e "${RED}❌ MinIO failed to start${NC}"
    exit 1
fi

echo ""

# Step 2: Create virtual environment
echo "🐍 Step 2: Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Step 3: Install dependencies
echo "📦 Step 3: Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -e . > /dev/null 2>&1
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 4: Install pgvector extension
echo "🔧 Step 4: Installing pgvector extension..."
docker exec -it altcare_postgres psql -U altcare -d altcare_dev -c "CREATE EXTENSION IF NOT EXISTS vector;" > /dev/null 2>&1
echo -e "${GREEN}✅ pgvector extension installed${NC}"
echo ""

# Step 5: Create and run migrations
echo "🗄️  Step 5: Creating database migrations..."

# Check if migrations already exist
if [ -n "$(ls -A alembic/versions/ 2>/dev/null)" ]; then
    echo -e "${YELLOW}⚠️  Migrations already exist, skipping creation${NC}"
else
    alembic revision --autogenerate -m "Initial schema with 30 tables"
    echo -e "${GREEN}✅ Migration created${NC}"
fi

echo "🗄️  Applying migrations..."
alembic upgrade head
echo -e "${GREEN}✅ Database schema created (30 tables)${NC}"
echo ""

# Step 6: Verify setup
echo "✨ Step 6: Verifying setup..."
TABLE_COUNT=$(docker exec -it altcare_postgres psql -U altcare -d altcare_dev -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' \n')

if [ "$TABLE_COUNT" -ge "30" ]; then
    echo -e "${GREEN}✅ Database has $TABLE_COUNT tables${NC}"
else
    echo -e "${RED}❌ Expected 30+ tables but found $TABLE_COUNT${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment:"
echo "     ${YELLOW}source venv/bin/activate${NC}"
echo ""
echo "  2. Start the development server:"
echo "     ${YELLOW}uvicorn app.main:app --reload${NC}"
echo ""
echo "  3. Open API documentation:"
echo "     ${YELLOW}http://localhost:8000/docs${NC}"
echo ""
echo "  4. MinIO Console (file storage):"
echo "     ${YELLOW}http://localhost:9001${NC} (minioadmin / minioadmin)"
echo ""
echo "Happy coding! 🚀"
