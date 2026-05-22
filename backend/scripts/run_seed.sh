#!/bin/bash
# Quick script to run database seeding

set -e

echo "🌱 AltCare Database Seeding Script"
echo "=================================="
echo ""

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
