#!/bin/bash
set -e

# Initialize database and seed users if needed
echo "📦 Running database initialization..."
python init_admin.py

echo ""
echo "🚀 Starting API server..."
exec "$@"
