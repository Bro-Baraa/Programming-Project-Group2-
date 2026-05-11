#!/bin/bash
# Quick test runner - run from backend directory

# Determine script location and cd to backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.." || exit 1

python -m pytest tests/ -v --tb=short "$@"