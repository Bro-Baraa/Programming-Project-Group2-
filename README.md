# Stage Monitoring Tool

Een compleet stagevolgsysteem voor de opleiding Toegepaste Informatica (Erasmus Hogeschool Brussel).

- **Frontend**: HTML/CSS/JS met API-integratie (`frontend/`)
- **Backend**: FastAPI + SQLite REST API (`backend/`)
- **Authenticatie**: JWT-tokens met rolgebaseerde toegang

## 🚀 Snelle Start

### Optie 1: Alles tegelijk starten

```bash
./start.sh
```

Dit start:
- **Backend API**: http://localhost:8001
- **Frontend**: http://localhost:8080

Ga dan naar **http://localhost:8080**

### Optie 2: Handmatig

**Terminal 1 — Backend:**
```bash
cd backend
python init_admin.py        # Eerste keer: database + testgebruikers
uvicorn app.main:app --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
python3 -m http.server 8080
```

Bezoek http://localhost:8080

### Optie 3: Alleen backend (voor API-testen)
```bash
cd backend
python init_admin.py
uvicorn app.main:app --reload
```

Swagger docs: http://localhost:8001/docs

---

## 🔐 Eerste keer instellen

```bash
cd backend
cp .env.example .env          # Maak een lokale env aan
python init_admin.py         # Maakt database en testgebruikers
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

## 📁 Projectstructuur

```
prog-project-wt2/
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
│   ├── init_admin.py            # Eerste keer setup
│   ├── seed_complete.py         # Testdata seeding
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Template voor env-variabelen
│   └── pytest.ini               # Testconfiguratie
├── docs/                         # Projectdocumentatie
│   ├── architectuur.md            # Backend-architectuur
│   ├── feature-todo.md            # Ontbrekende features
│   └── analyses/                # Groepsanalyses
└── .gitignore
```

---

## 🧪 Testen

### Backend tests
```bash
cd backend
pytest
```

### Testdata seeden
```bash
cd backend
python seed_complete.py
```

---

## 🔧 Veelvoorkomende problemen

**`RuntimeError: SECRET_KEY environment variable must be set`**  
→ Kopieer `backend/.env.example` naar `backend/.env` en pas `SECRET_KEY` aan.

**CORS-fouten**  
→ Zorg dat je de frontend benadert via `http://localhost:8080`, niet `file://`.

**Database vergrendeld**  
→ Stop de backend, verwijder `backend/stage_monitoring.db`, en voer opnieuw `init_admin.py` uit.

---

## 📄 Licentie

Schoolproject — Groep 2