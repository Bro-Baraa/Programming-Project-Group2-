#!/bin/bash
set -e

echo "========================================"
echo "  Stage Monitoring Tool — Docker Start"
echo "========================================"
echo ""
echo "Python:    $(python3 --version)"
echo "Database:  $DATABASE_PATH"
echo "Frontend:  /app/frontend"
echo ""

# Create data dir if it doesn't exist
mkdir -p "$(dirname "$DATABASE_PATH")"

# Seed database if empty
if [ ! -f "$DATABASE_PATH" ]; then
    echo "📦 Database not found. Running seed..."
    cd /app/backend
    python3 seed_loader.py
    echo ""
fi

echo "🚀 Starting API + Frontend on port 8080..."
echo ""
exec "$@"
