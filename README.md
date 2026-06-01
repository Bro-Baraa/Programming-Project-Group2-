# Stage Monitoring Tool

Een compleet stagevolgsysteem voor de opleiding Toegepaste Informatica (Erasmus Hogeschool Brussel).

- **Frontend**: HTML/CSS/JS met API-integratie (`frontend/`)
- **Backend**: FastAPI + SQLite REST API (`backend/`)
- **Authenticatie**: JWT-tokens met rolgebaseerde toegang

## Snelle Start

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

Ga dan naar **http://localhost:8080**

> **Windows opmerking:** Je hebt Python nodig (download via [python.org](https://python.org)). De script maakt automatisch een virtuele omgeving en installeert alles. Geen `uv` of Node.js nodig.

### Optie 2: Handmatig

**Terminal 1 — Backend:**
```bash
cd backend
cp .env.example .env        # Windows: copy .env.example .env
python init_admin.py        # Eerste keer: database + testgebruikers
uvicorn app.main:app --reload
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
uvicorn app.main:app --reload
```

Swagger docs: http://localhost:8001/docs

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
├── frontend/                     # Frontend applicatie
│   ├── index.html               # Hoofdpagina met alle UI-templates
│   ├── app.js                   # Kernlogica: views, formulieren, API-calls
│   ├── api-client.js            # Herbruikbare API-client modules
│   ├── styles.css               # Gedeelde stijlen
│   ├── prototype/               # Archief: oude prototype-versies
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
│   ├── seed.py                  # Testdata seeding (basis)
│   ├── seed_complete.py         # Testdata seeding (uitgebreid)
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Template voor env-variabelen
│   └── pytest.ini               # Testconfiguratie
├── docs/                         # Projectdocumentatie
│   ├── architectuur.md          # Backend-architectuur
│   ├── feature-todo.md          # Ontbrekende features
│   └── analyses/                # Groepsanalyses
├── start.sh                     # Start backend + frontend tegelijk
└── .gitignore
```

---

## Testen

### Backend tests
```bash
cd backend
pytest
```

### Testdata seeden
```bash
cd backend
python seed.py          # basis users + competenties
python seed_complete.py  # uitgebreidere testdata
```

> **Windows:** Gebruik `python` in plaats van `python3` en `pytest` via `python -m pytest` als het commando niet in PATH staat.