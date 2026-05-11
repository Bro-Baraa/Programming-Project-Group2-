#!/bin/bash
# Test runner script for Stage Monitoring Tool

set -e

echo "🧪 Stage Monitoring Tool - Test Runner"
echo "======================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
elif [ -d "venv" ] && [ -f "venv/Scripts/activate" ]; then
    echo "📦 Activating virtual environment (Windows)..."
    source venv/Scripts/activate
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing test dependencies..."
    pip install pytest httpx
fi

echo ""
echo "🏃 Running tests..."
echo ""

# Run tests with verbose output and coverage if available
if python -m pytest --version | grep -q "pytest"; then
    python -m pytest tests/ -v --tb=short -W ignore::DeprecationWarning "$@"
else
    echo "❌ pytest not available. Please install: pip install pytest"
    exit 1
fi

echo ""
echo "✅ Tests completed!"