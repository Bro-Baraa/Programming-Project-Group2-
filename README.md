# Stage Monitoring Tool

Een compleet stagevolgsysteem voor de opleiding Toegepaste Informatica (Erasmus Hogeschool Brussel).

- **Frontend**: HTML/CSS/JS met API-integratie (`frontend/`)
- **Backend**: FastAPI + SQLite REST API (`backend/`)
- **Authenticatie**: JWT-tokens met rolgebaseerde toegang

---

## Snelle Start (Lokaal)

### Optie 1: Alles tegelijk starten

**macOS / Linux:**
```bash
./start.sh
```

**Windows:**
```batch
start.bat
```
Of dubbelklik op `start.bat` in de Verkenner.

Dit start:
- **Backend API**: http://localhost:8001
- **Frontend**: http://localhost:8080

De browser opent automatisch. Zo niet, ga dan naar **http://localhost:8080**.

> **⚠️ Belangrijk:** Open `index.html` niet rechtstreeks in de Verkenner. De app moet altijd via `http://localhost:8080` bereikt worden, anders werkt het inloggen niet.

> **Windows opmerking:** Je hebt Python nodig (download via [python.org](https://python.org)). Het script maakt automatisch een virtuele omgeving en installeert alles. Geen `uv` of Node.js nodig.

### Optie 2: Handmatig

**Terminal 1 — Backend:**
```bash
cd backend
cp .env.example .env        # Windows: copy .env.example .env
python init_admin.py        # Eerste keer: database + testgebruikers
uvicorn app.main:app --reload --port 8001
```

**Terminal 2 — Frontend:**
```bash
cd frontend
python3 -m http.server 8080   # Windows: python -m http.server 8080
```

Bezoek http://localhost:8080

### Optie 3: Alleen backend (voor API-testen)
```bash
cd backend
cp .env.example .env
python init_admin.py
uvicorn app.main:app --reload --port 8001
```

Swagger docs: http://localhost:8001/docs

---

## Deployen

### Docker (lokaal of server)

```bash
# Bouwen en starten
docker compose up --build

# Of op de achtergrond
docker compose up -d

# Stoppen
docker compose down
```

De app draait dan op **http://localhost:8080** (backend + frontend in één container). Data wordt bewaard in een named volume (`stage-data`).

### Fly.io

```bash
# Eerste keer: app aanmaken (al gedaan voor dit project)
# fly launch

# Deployen
fly deploy
```

De app draait op **https://stage-monitoring-demo.fly.dev** (of jouw app-naam).

> **Productie-hardening:** De Fly.io-deploy is beveiligd tegen scrapers:
> - Swagger UI (`/docs`) en OpenAPI schema (`/openapi.json`) zijn uitgeschakeld
> - `/auth/login`, `/auth/register` en `/health` hebben rate limiting (10 req/min per IP)
> - `robots.txt` blokkeert crawlers
> - VM is ingesteld op 256MB RAM (kostenbesparing)

Wil je `/docs` tijdelijk inschakelen (bijv. voor debugging), pas dan `backend/app/main.py` aan:
```python
app = FastAPI(..., docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json")
```

---

## Eerste keer instellen

**macOS / Linux:**
```bash
cd backend
cp .env.example .env
python init_admin.py
```

**Windows:**
```batch
cd backend
copy .env.example .env
python init_admin.py
```

### Testaccounts

| Rol | E-mail | Wachtwoord |
|-----|--------|------------|
| Admin | admin@school.be | admin123 |
| Student | student1@school.be | student123 |
| Commissie | commissie1@school.be | commissie123 |
| Docent | docent1@school.be | docent123 |
| Mentor | mentor1@school.be | mentor123 |

---

## Projectstructuur

```
Programming-Project-Group2-/
├── frontend/                     # Frontend applicatie (statische HTML/JS)
│   ├── index.html               # Hoofdpagina met alle UI-templates
│   ├── app.js                   # Kernlogica: views, formulieren, API-calls
│   ├── api-client.js            # Herbruikbare API-client modules
│   ├── styles.css               # Gedeelde stijlen
│   ├── table-cards.js           # Tabel-kaart component
│   ├── ui-helpers.js            # UI utility functies
│   └── README.md                # Frontend-specifieke documentatie
├── backend/                      # FastAPI Backend
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models.py            # Database-modellen
│   │   ├── auth.py              # JWT + wachtwoord hashing
│   │   ├── dependencies.py      # Gedeelde FastAPI dependencies
│   │   ├── routers/             # API endpoints per domein
│   │   ├── schemas/             # Pydantic request/response schema's
│   │   └── services/            # Business logic
│   ├── tests/                   # pytest testsuite
│   ├── uploads/agreements/      # PDF uploads
│   ├── init_admin.py            # Eerste keer setup
│   ├── seed.py                  # Testdata seeding (alias → seed_loader.py)
│   ├── seed_loader.py            # Testdata seeding (YAML-backed, core)
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Template voor env-variabelen
│   └── pytest.ini               # Testconfiguratie
├── docs/                         # Projectdocumentatie
│   ├── architectuur.md          # Backend-architectuur
│   ├── feature-todo.md          # Ontbrekende features
│   └── analyses/                # Groepsanalyses
├── Dockerfile                    # Docker build (single container)
├── docker-compose.yml            # Docker Compose config
├── docker-entrypoint.sh          # Docker startup script
├── docker_main.py                # Docker entrypoint (FastAPI + static files)
├── fly.toml                      # Fly.io deploy config
├── start.sh                      # Start backend + frontend tegelijk (Unix)
├── start.bat                     # Start backend + frontend tegelijk (Windows)
└── .gitignore
```

---

## Testen

### Backend tests
```bash
cd backend
pytest
```

### Test runner script
```bash
cd backend
./run_tests.sh
```

### Testdata seeden
```bash
cd backend
python seed_loader.py   # uitgebreide testdata (YAML-backed)
# of: python seed.py     # alias voor hetzelfde
```

> **Windows:** Gebruik `python` in plaats van `python3` en `pytest` via `python -m pytest` als het commando niet in PATH staat.

---

## Environment Variables

Kopieer `backend/.env.example` naar `backend/.env` en pas aan:

```bash
SECRET_KEY=een-willekeurige-string-hier
DATABASE_PATH=stage_monitoring.db
FRONTEND_ORIGINS=http://localhost:8080
```

- `SECRET_KEY` — Vereist voor JWT tokens. **Wijzig voor productie!**
- `DATABASE_PATH` — Pad naar SQLite database (standaard: `stage_monitoring.db`)
- `FRONTEND_ORIGINS` — Comma-separated lijst van toegestane frontend URLs voor CORS. Gebruik `*` voor development (niet aanbevolen voor productie).

---

## Belangrijke Endpoints

| Domein | Endpoints |
|--------|-----------|
| Auth | `POST /auth/login`, `POST /auth/register`, `GET /auth/me` |
| Internships | `GET /internships`, `POST /internships`, `GET /internships/{id}` |
| Proposals | `PATCH /internships/{id}/proposal`, `POST /internships/{id}/resubmit` |
| Agreements | `POST /internships/{id}/agreement`, `PATCH /internships/{id}/agreement` |
| Logbooks | `GET /internships/{id}/logbooks`, `POST /internships/{id}/logbooks`, `PATCH /internships/logbooks/{id}` |
| Evaluations | `GET /internships/{id}/evaluations`, `POST /internships/{id}/evaluations`, `POST /evaluations/{id}/finalize` |
| Competencies | `GET /competencies`, `POST /competencies/profiles`, `POST /competencies` |
| Feedback | `GET /internships/{id}/feedback`, `POST /internships/{id}/feedback` |
| Audit | `GET /audit` |
| Dashboard | `GET /me/dashboard`, `GET /internships/stats/dashboard` |
| Users | `GET /users`, `GET /users/{id}` |

Zie `/docs` (lokaal) voor de volledige lijst.

---

## Opmerkingen

- Statusovergangen worden gevalideerd in `app/services/lifecycle.py`
- Een stage kan pas naar "Lopend" als de overeenkomst is gevalideerd
- PDFs worden opgeslagen in `uploads/agreements/`
- JWT tokens verlopen na 24 uur
- SQLite is de standaard database (geen setup nodig). Voor PostgreSQL/MySQL: pas `SQLALCHEMY_DATABASE_URL` in `app/database.py` aan.
- Alle belangrijke acties worden gelogd in de `audit_logs` tabel en zijn raadpleegbaar via `GET /audit` (enkel admin). Zie `backend/README.md` voor de volledige lijst van events.
