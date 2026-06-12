#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT=8001
FRONTEND_PORT=8080

RESET_DB=false
BACKEND_ONLY=false
FRONTEND_ONLY=false

for arg in "$@"; do
  case "$arg" in
    --reset) RESET_DB=true ;;
    --backend) BACKEND_ONLY=true ;;
    --frontend) FRONTEND_ONLY=true ;;
    --help|-h)
      echo "Usage: ./start.sh [options]"
      echo ""
      echo "Options:"
      echo "  (none)      Start backend + frontend"
      echo "  --reset     Reset database and seed"
      echo "  --backend   Start backend only"
      echo "  --frontend  Start frontend only"
      echo "  --help      Show this help"
      exit 0
      ;;
  esac
done

if [ ! -f "$PROJECT_DIR/backend/.env" ] && [ -f "$PROJECT_DIR/backend/.env.example" ]; then
  RANDOM_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
  sed "s/^SECRET_KEY=.*/SECRET_KEY=${RANDOM_KEY}/" "$PROJECT_DIR/backend/.env.example" > "$PROJECT_DIR/backend/.env"
  echo ".env created from .env.example"
fi

USE_UV=false
PYTHON_RUNNER="python3"

if command -v uv >/dev/null 2>&1; then
  USE_UV=true
fi

if [ "$USE_UV" = true ]; then
  if [ ! -d "$PROJECT_DIR/backend/.venv" ]; then
    cd "$PROJECT_DIR/backend"
    uv venv
  fi
  PYTHON_RUNNER="uv run -- python"
  INIT_RUNNER="uv run -- python"
else
  if [ -f "$PROJECT_DIR/backend/.venv/bin/python" ]; then
    PYTHON_RUNNER="$PROJECT_DIR/backend/.venv/bin/python"
    INIT_RUNNER="$PROJECT_DIR/backend/.venv/bin/python"
  else
    INIT_RUNNER="$PYTHON_RUNNER"
  fi
fi

if [ "$BACKEND_ONLY" = false ]; then
  if ! command -v node >/dev/null 2>&1; then
    echo "Node.js not found. Install from https://nodejs.org"
    exit 1
  fi
  if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
    cd "$PROJECT_DIR/frontend"
    npm install
  fi
fi

cd "$PROJECT_DIR/backend"
if ! $PYTHON_RUNNER -c "import uvicorn, fastapi, sqlalchemy, pydantic, dotenv" 2>/dev/null; then
  if [ "$USE_UV" = true ]; then
    uv pip install -r requirements.txt
  else
    $PYTHON_RUNNER -m pip install -r requirements.txt
  fi
fi

DB_FILE="$PROJECT_DIR/backend/stage_monitoring.db"

if [ "$RESET_DB" = true ] && [ -f "$DB_FILE" ]; then
  rm -f "$DB_FILE"
  echo "Database reset"
fi

if [ ! -f "$DB_FILE" ]; then
  $PYTHON_RUNNER -c "
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
" 2>/dev/null || echo "Warning: failed to create tables"
  $INIT_RUNNER seed_loader.py
  echo "Database seeded"
fi

if [ "$FRONTEND_ONLY" = false ]; then
  cd "$PROJECT_DIR/backend"
  $PYTHON_RUNNER -m uvicorn app.main:app --reload \
    --reload-exclude "*.db" --reload-exclude "*.db-journal" \
    --reload-exclude "__pycache__" --reload-exclude "*.pyc" \
    --port $BACKEND_PORT --host 0.0.0.0 &
fi

if [ "$BACKEND_ONLY" = false ]; then
  cd "$PROJECT_DIR/frontend"
  if [ -f "$PROJECT_DIR/frontend/node_modules/.bin/vite" ]; then
    "$PROJECT_DIR/frontend/node_modules/.bin/vite" --host &
  else
    npx vite --host &
  fi
fi

echo ""
echo "========================================"
if [ "$FRONTEND_ONLY" = false ]; then
  echo "Backend:  http://localhost:$BACKEND_PORT"
fi
if [ "$BACKEND_ONLY" = false ]; then
  echo "Frontend: http://localhost:$FRONTEND_PORT"
fi
echo ""
echo "Ctrl+C to stop"
echo "========================================"
echo ""

wait
