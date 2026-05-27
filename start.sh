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
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stage Monitoring Tool — Startscript${NC}"
echo "===================================="
echo ""

# Check if .env exists, auto-create from example with random SECRET_KEY if not
if [ ! -f "$PROJECT_DIR/backend/.env" ]; then
    if [ -f "$PROJECT_DIR/backend/.env.example" ]; then
        echo -e "${YELLOW}backend/.env niet gevonden. Auto-aanmaken uit .env.example...${NC}"
        # Generate a random 32-char SECRET_KEY and replace the placeholder
        RANDOM_KEY=$(openssl rand -hex 16 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(16))")
        sed "s/^SECRET_KEY=.*/SECRET_KEY=${RANDOM_KEY}/" "$PROJECT_DIR/backend/.env.example" > "$PROJECT_DIR/backend/.env"
        echo -e "${GREEN}backend/.env aangemaakt met een willekeurige SECRET_KEY.${NC}"
        echo ""
    else
        echo -e "${RED}Waarschuwing: backend/.env noch backend/.env.example gevonden.${NC}"
        echo "SECRET_KEY moet handmatig worden ingesteld."
        echo ""
    fi
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
USE_UV=false
if command -v uv >/dev/null 2>&1; then
    USE_UV=true
    echo -e "${BLUE}uv gedetecteerd${NC}"
else
    echo -e "${BLUE}uv niet gevonden${NC}"
fi

if [ "$USE_UV" = true ]; then
    if [ ! -d "$PROJECT_DIR/backend/.venv" ]; then
        echo -e "${YELLOW}Virtuele omgeving niet gevonden. Aanmaken met uv...${NC}"
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
        PYTHON_RUNNER="python3"
        INIT_RUNNER="python3"
    fi
    echo -e "${BLUE}Gebruik: $PYTHON_RUNNER${NC}"
fi

# Check and install dependencies if missing
echo -e "${BLUE}Controleren of afhankelijkheden geïnstalleerd zijn...${NC}"
cd "$PROJECT_DIR/backend"
if ! $PYTHON_RUNNER -c "import uvicorn, fastapi, sqlalchemy" 2>/dev/null; then
    echo -e "${YELLOW}Afhangelijkheden ontbreken. Installeren uit requirements.txt...${NC}"
    if [ "$USE_UV" = true ]; then
        uv pip install -r requirements.txt
    else
        if [ ! -d "$PROJECT_DIR/backend/.venv" ]; then
            echo -e "${YELLOW}Virtuele omgeving aanmaken...${NC}"
            python3 -m venv .venv
            PYTHON_RUNNER="$PROJECT_DIR/backend/.venv/bin/python"
            INIT_RUNNER="$PROJECT_DIR/backend/.venv/bin/python"
        fi
        if [ -f "$PROJECT_DIR/backend/.venv/bin/pip" ]; then
            "$PROJECT_DIR/backend/.venv/bin/pip" install -r requirements.txt
        else
            echo -e "${RED}pip niet gevonden in virtuele omgeving. Probeer opnieuw:${NC}"
            echo "  rm -rf backend/.venv && ./start.sh"
            exit 1
        fi
    fi
    echo -e "${GREEN}Afhangelijkheden geïnstalleerd.${NC}"
fi

# Check if database is empty and seed if needed
DB_FILE="$PROJECT_DIR/backend/stage_monitoring.db"
if [ ! -f "$DB_FILE" ] || ! $INIT_RUNNER -c "
import sqlite3, sys
conn = sqlite3.connect('$DB_FILE')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM users;')
count = cursor.fetchone()[0]
conn.close()
sys.exit(0 if count > 0 else 1)
" 2>/dev/null; then
    echo -e "${YELLOW}Database leeg of niet gevonden. Seeding met demo-data...${NC}"
    cd "$PROJECT_DIR/backend"
    $INIT_RUNNER seed_complete.py
    echo -e "${GREEN}Database gevuld!${NC}"
    echo ""
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
        echo "  cd backend && uv pip install -r requirements.txt"
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
