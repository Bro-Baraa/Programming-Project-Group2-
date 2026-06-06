#!/bin/bash
# Stage Monitoring Tool — Ontwikkelstartscript
# Cross-platform: macOS, Linux, WSL
# Start backend (FastAPI) + frontend (Vite dev server) in één keer
#
# Gebruik:
#   ./start.sh              Start backend + frontend
#   ./start.sh --reset      Reset database + seed
#   ./start.sh --backend    Start alleen backend
#   ./start.sh --frontend   Start alleen frontend
#   ./start.sh --help       Toon help

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT=8001
FRONTEND_PORT=8080

# ── Kleuren ───────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── Argumenten ───────────────────────────────────────────────────────────
RESET_DB=false
BACKEND_ONLY=false
FRONTEND_ONLY=false
HELP=false

for arg in "$@"; do
  case "$arg" in
    --reset) RESET_DB=true ;;
    --backend) BACKEND_ONLY=true ;;
    --frontend) FRONTEND_ONLY=true ;;
    --help) HELP=true ;;
    -h) HELP=true ;;
  esac
done

if [ "$HELP" = true ]; then
  echo -e "${CYAN}Stage Monitoring Tool — Ontwikkelstartscript${NC}"
  echo ""
  echo "Gebruik: ./start.sh [opties]"
  echo ""
  echo "Opties:"
  echo "  (geen)       Start backend + frontend"
  echo "  --reset      Reset database en vul opnieuw met demodata"
  echo "  --backend    Start alleen backend API server"
  echo "  --frontend   Start alleen frontend dev server"
  echo "  --help       Toon deze help"
  echo ""
  echo "Vereisten:"
  echo "  • Python 3.10+ (met pip of uv)"
  echo "  • Node.js 18+ (voor Vite dev server)"
  echo ""
  echo "Testaccounts:"
  echo "  admin@school.be      / demo123"
  echo "  docent1@school.be    / docent123"
  echo "  student1@school.be   / student123"
  echo ""
  exit 0
fi

# ── Header ───────────────────────────────────────────────────────────────
echo -e "${CYAN}Stage Monitoring Tool — Ontwikkelstartscript${NC}"
echo "================================================"
echo ""

# ── Check .env ───────────────────────────────────────────────────────────
if [ ! -f "$PROJECT_DIR/backend/.env" ]; then
  if [ -f "$PROJECT_DIR/backend/.env.example" ]; then
    echo -e "${YELLOW}backend/.env niet gevonden. Aanmaken uit .env.example...${NC}"
    RANDOM_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32 2>/dev/null || date +%s%N | sha256sum | head -c 64)
    sed "s/^SECRET_KEY=.*/SECRET_KEY=${RANDOM_KEY}/" "$PROJECT_DIR/backend/.env.example" > "$PROJECT_DIR/backend/.env"
    echo -e "${GREEN}✓ .env aangemaakt met willekeurige SECRET_KEY${NC}"
    echo ""
  else
    echo -e "${RED}Waarschuwing: .env.example niet gevonden. Sommige functies werken mogelijk niet.${NC}"
    echo ""
  fi
fi

# ── Bepaal Python runner ───────────────────────────────────────────────
USE_UV=false
PYTHON_RUNNER="python3"
PIP_RUNNER="pip3"

if command -v uv >/dev/null 2>&1; then
  USE_UV=true
  echo -e "${BLUE}uv gedetecteerd${NC}"
else
  echo -e "${BLUE}uv niet gevonden, gebruik python3${NC}"
fi

if [ "$USE_UV" = true ]; then
  if [ ! -d "$PROJECT_DIR/backend/.venv" ]; then
    echo -e "${YELLOW}Virtuele omgeving aanmaken met uv...${NC}"
    cd "$PROJECT_DIR/backend"
    uv venv
  fi
  PYTHON_RUNNER="uv run -- python"
  INIT_RUNNER="uv run -- python"
else
  if [ -f "$PROJECT_DIR/backend/.venv/bin/python" ]; then
    PYTHON_RUNNER="$PROJECT_DIR/backend/.venv/bin/python"
    INIT_RUNNER="$PROJECT_DIR/backend/.venv/bin/python"
    PIP_RUNNER="$PROJECT_DIR/backend/.venv/bin/pip"
    echo -e "${BLUE}Gebruik .venv/bin/python${NC}"
  fi
fi

# ── Check Node.js ───────────────────────────────────────────────────────
if [ "$BACKEND_ONLY" = false ]; then
  if ! command -v node >/dev/null 2>&1; then
    echo -e "${RED}Node.js niet gevonden! Installeer via https://nodejs.org${NC}"
    echo -e "${YELLOW}Of voer uit: ./start.sh --backend${NC} om alleen backend te starten"
    echo ""
    exit 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    echo -e "${RED}npm niet gevonden! Dit hoort bij Node.js.${NC}"
    exit 1
  fi
  # Installeer frontend deps indien nodig
  if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
    echo -e "${YELLOW}Frontend afhankelijkheden installeren...${NC}"
    cd "$PROJECT_DIR/frontend"
    npm install
    echo -e "${GREEN}✓ Frontend deps geïnstalleerd${NC}"
    echo ""
  fi
fi

# ── Check backend deps ─────────────────────────────────────────────────
echo -e "${BLUE}Backend afhankelijkheden controleren...${NC}"
cd "$PROJECT_DIR/backend"
if ! $PYTHON_RUNNER -c "import uvicorn, fastapi, sqlalchemy, pydantic, dotenv" 2>/dev/null; then
  echo -e "${YELLOW}Backend afhankelijkheden installeren...${NC}"
  if [ "$USE_UV" = true ]; then
    uv pip install -r requirements.txt
  else
    if [ ! -f "$PROJECT_DIR/backend/.venv/bin/pip" ]; then
      $PYTHON_RUNNER -m pip install -r requirements.txt
    else
      $PIP_RUNNER install -r requirements.txt
    fi
  fi
  echo -e "${GREEN}✓ Backend deps geïnstalleerd${NC}"
  echo ""
fi

# ── Database ─────────────────────────────────────────────────────────────
DB_FILE="$PROJECT_DIR/backend/stage_monitoring.db"

if [ "$RESET_DB" = true ]; then
  echo -e "${YELLOW}Database resetten...${NC}"
  if [ -f "$DB_FILE" ]; then
    rm -f "$DB_FILE"
    echo -e "${GREEN}✓ Databasebestand verwijderd${NC}"
  fi
fi

# Check of database aangemaakt/ge seeded moet worden
if [ ! -f "$DB_FILE" ]; then
  echo -e "${YELLOW}Database niet gevonden. Tabellen aanmaken...${NC}"
  $PYTHON_RUNNER -c "
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
print('Tabellen aangemaakt.')
" 2>/dev/null || echo -e "${RED}Tabellen aanmaken mislukt. Controleer of modellen correct importeren.${NC}"
  echo -e "${YELLOW}Database vullen met demodata...${NC}"
  $INIT_RUNNER seed_loader.py
  echo -e "${GREEN}✓ Database gevuld${NC}"
  echo ""
else
  # Check of leeg
  USER_COUNT=$($INIT_RUNNER -c "
import sqlite3
conn = sqlite3.connect('$DB_FILE')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM users')
count = cursor.fetchone()[0]
conn.close()
print(count)
" 2>/dev/null || echo "0")
  if [ "$USER_COUNT" = "0" ] || [ -z "$USER_COUNT" ]; then
    echo -e "${YELLOW}Database leeg. Vullen...${NC}"
    $INIT_RUNNER seed_loader.py
    echo -e "${GREEN}✓ Database gevuld${NC}"
    echo ""
  fi
fi

# ── Poort opruimen ────────────────────────────────────────────────────────
if [ "$FRONTEND_ONLY" = false ]; then
  BACKEND_PID_OLD=$(lsof -ti :$BACKEND_PORT 2>/dev/null || true)
  if [ -n "$BACKEND_PID_OLD" ]; then
    echo -e "${YELLOW}Poort $BACKEND_PORT in gebruik. Oude backend afsluiten...${NC}"
    kill -9 $BACKEND_PID_OLD 2>/dev/null || true
    sleep 0.5
  fi
fi

if [ "$BACKEND_ONLY" = false ]; then
  FRONTEND_PID_OLD=$(lsof -ti :$FRONTEND_PORT 2>/dev/null || true)
  if [ -n "$FRONTEND_PID_OLD" ]; then
    echo -e "${YELLOW}Poort $FRONTEND_PORT in gebruik. Oude frontend afsluiten...${NC}"
    kill -9 $FRONTEND_PID_OLD 2>/dev/null || true
    sleep 0.5
  fi
fi

# ── Start backend ───────────────────────────────────────────────────────
if [ "$FRONTEND_ONLY" = false ]; then
  echo -e "${GREEN}Backend starten op http://localhost:$BACKEND_PORT${NC}"
  cd "$PROJECT_DIR/backend"
  $PYTHON_RUNNER -m uvicorn app.main:app --reload --port $BACKEND_PORT --host 0.0.0.0 &
  BACKEND_PID=$!
  sleep 2

  if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Backend starten mislukt!${NC}"
    exit 1
  fi
fi

# ── Start frontend ───────────────────────────────────────────────────────
if [ "$BACKEND_ONLY" = false ]; then
  echo -e "${GREEN}Frontend starten op http://localhost:$FRONTEND_PORT${NC}"
  cd "$PROJECT_DIR/frontend"
  npm run dev &
  FRONTEND_PID=$!
  sleep 2
fi

# ── Browser openen ───────────────────────────────────────────────────────
if [ "$BACKEND_ONLY" = false ]; then
  sleep 1
  URL="http://localhost:$FRONTEND_PORT"
  if command -v open >/dev/null 2>&1; then
    open "$URL" 2>/dev/null || true
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" 2>/dev/null || true
  fi
fi

# ── Samenvatting ─────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✓ Alles draait!${NC}"
echo ""
if [ "$FRONTEND_ONLY" = false ]; then
  echo "  Backend:   http://localhost:$BACKEND_PORT"
  echo "  API docs:  http://localhost:$BACKEND_PORT/docs"
fi
if [ "$BACKEND_ONLY" = false ]; then
  echo "  Frontend:  http://localhost:$FRONTEND_PORT"
fi
echo ""
echo "Testaccounts:"
echo "  admin@school.be      / demo123"
echo "  docent1@school.be    / docent123"
echo "  mentor1@school.be    / mentor123"
echo "  student1@school.be   / student123"
echo "  commissie1@school.be / commissie123"
echo ""
echo "Druk Ctrl+C om te stoppen"
echo -e "${GREEN}================================================${NC}"
echo ""

# ── Afsluiten ────────────────────────────────────────────────────────────
cleanup() {
  echo ""
  echo -e "${YELLOW}Afsluiten...${NC}"
  if [ "$FRONTEND_ONLY" = false ]; then
    kill $BACKEND_PID 2>/dev/null || true
  fi
  if [ "$BACKEND_ONLY" = false ]; then
    kill $FRONTEND_PID 2>/dev/null || true
  fi
  wait 2>/dev/null || true
  echo -e "${GREEN}Gestopt.${NC}"
}
trap cleanup EXIT INT TERM

# ── Wachten ──────────────────────────────────────────────────────────────
wait
