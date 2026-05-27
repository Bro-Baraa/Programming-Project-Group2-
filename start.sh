#!/bin/bash
# Start alles: backend API + frontend server
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT=8001
FRONTEND_PORT=8080

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stage Monitoring Tool — Startscript${NC}"
echo "===================================="
echo ""

# Check if .env exists, warn if not
if [ ! -f "$PROJECT_DIR/backend/.env" ]; then
    echo -e "${RED}Waarschuwing: backend/.env niet gevonden.${NC}"
    echo "Kopieer backend/.env.example naar backend/.env en pas SECRET_KEY aan."
    echo ""
    echo "Voorbeeld:"
    echo "  cp backend/.env.example backend/.env"
    echo ""
fi

# Check if database exists, suggest init
if [ ! -f "$PROJECT_DIR/backend/stage_monitoring.db" ]; then
    echo -e "${RED}Database niet gevonden. Eerste keer setup nodig:${NC}"
    echo "  cd backend && $INIT_RUNNER init_admin.py"
    echo ""
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${BLUE}Servers stoppen...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}Gestopt.${NC}"
}
trap cleanup EXIT INT TERM

# Determine Python runner: prefer uv, fall back to .venv/bin/python
if command -v uv >/dev/null 2>&1; then
    PYTHON_RUNNER="uv run -- python"
    INIT_RUNNER="uv run -- python"
    echo -e "${BLUE}uv gedetecteerd — gebruik uv run${NC}"
else
    if [ -f "$PROJECT_DIR/backend/.venv/bin/python" ]; then
        PYTHON_RUNNER="$PROJECT_DIR/backend/.venv/bin/python"
        INIT_RUNNER="$PROJECT_DIR/backend/.venv/bin/python"
    else
        PYTHON_RUNNER="python3"
        INIT_RUNNER="python3"
    fi
    echo -e "${BLUE}uv niet gevonden — gebruik: $PYTHON_RUNNER${NC}"
fi

# Start backend
echo -e "${GREEN}Backend starten op http://localhost:$BACKEND_PORT${NC}"
cd "$PROJECT_DIR/backend"
$PYTHON_RUNNER -m uvicorn app.main:app --reload --port $BACKEND_PORT &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Check if backend started
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Backend kon niet starten. Controleer of uvicorn geïnstalleerd is:${NC}"
    if command -v uv >/dev/null 2>&1; then
        echo "  cd backend && uv sync"
    else
        echo "  cd backend && pip install -r requirements.txt"
    fi
    exit 1
fi

# Start frontend
echo -e "${GREEN}Frontend starten op http://localhost:$FRONTEND_PORT${NC}"
cd "$PROJECT_DIR/frontend"
python3 -m http.server $FRONTEND_PORT &
FRONTEND_PID=$!

sleep 1

echo ""
echo "===================================="
echo -e "${GREEN}✓ Alles draait!${NC}"
echo ""
echo "  Frontend:  http://localhost:$FRONTEND_PORT"
echo "  Backend:   http://localhost:$BACKEND_PORT"
echo "  API docs:  http://localhost:$BACKEND_PORT/docs"
echo ""
echo "Testaccounts:"
echo "  admin@school.be / admin123"
echo "  student1@school.be / student123"
echo ""
echo "Druk Ctrl+C om te stoppen."
echo ""

# Wait for both processes
wait
