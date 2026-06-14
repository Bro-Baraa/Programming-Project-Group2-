# Stage Monitoring Tool

Stagevolgsysteem voor Toegepaste Informatica (Erasmus Hogeschool Brussel).

**Stack:** FastAPI + SQLite backend, HTML/JS frontend (vanilla, geen build-stap vereist).

---

## Demo

Video's die de applicatie in actie tonen:

| # | Demo | Link |
|---|------|------|
| 1 | Installatie & opstarten | [Bekijk video](https://youtu.be/hzRFF7YV1s4) |
| 2 | Volledige rondleiding | [Bekijk video](https://youtu.be/Ul0cZwO2a4Q) |
| 3 | Stagevoorstel indienen | [Bekijk video](https://youtu.be/-PMWk7rEaf4) |

---

## Installatie & opstarten

### Optie 1 — `start.py` (aanbevolen, Windows & Linux)

Het startscript doet alles automatisch: het maakt een virtuele omgeving aan, installeert dependencies, vult de database indien leeg, en opent de browser.

**Vereisten:** Python 3.11+

```bash
# Windows
python start.py

# Linux / macOS
python3 start.py
```

Het script detecteert automatisch of `uv` beschikbaar is en gebruikt dat indien mogelijk. Zonder `uv` maakt het zelf een `.venv` aan via `python -m venv`.

De app is bereikbaar op **http://localhost:8001**.

> **Eerste keer?** `backend/.env` wordt automatisch aangemaakt vanuit `.env.example` met een willekeurige `SECRET_KEY`. Geen extra configuratie nodig voor lokaal gebruik.

---

### Optie 2 — Handmatig (Windows & Linux)

```bash
# 1. Virtuele omgeving aanmaken
cd backend
python -m venv .venv          # Windows
python3 -m venv .venv         # Linux / macOS

# 2. Activeren
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

# 3. Dependencies installeren
pip install -r requirements.txt

# 4. .env aanmaken
copy .env.example .env        # Windows
cp .env.example .env          # Linux / macOS

# 5. Database seeden
python seed_loader.py

# 6. Server starten
python -m uvicorn app.main:app --port 8001
```

De app is bereikbaar op **http://localhost:8001**.

> De frontend heeft **geen npm/build-stap nodig** — uvicorn serveert de `frontend/`-map rechtstreeks als statische bestanden.

---

### Optie 3 — Docker

**Vereisten:** Docker + Docker Compose

```bash
docker compose up          # builden en starten
docker compose up -d       # op de achtergrond
docker compose up --build  # herbouwen na codewijzigingen
docker compose down        # stoppen
```

De app is bereikbaar op **http://localhost:8080**.

Data wordt bewaard in een named volume (`stage-data`) en overleeft herstart.

Om een aangepaste `SECRET_KEY` mee te geven:

```bash
SECRET_KEY=mijn-geheime-sleutel docker compose up
```

---

### Testaccounts

Op het loginscherm staat een **"Test accounts laden"** knop die alle demo-accounts toont. Je kunt dan met één klik inloggen zonder wachtwoord in te vulken.

Of handmatig:

| Rol | E-mail | Wachtwoord |
|-----|--------|------------|
| Admin | admin@school.be | admin123 |
| Student | student1@school.be | student123 |
| Commissie | commissie1@school.be | commissie123 |
| Docent | docent1@school.be | docent123 |
| Mentor | mentor1@school.be | mentor123 |

---

### Testen

```bash
cd backend
pytest
```

## Projectstructuur

```
├── frontend/           # HTML/CSS/JS frontend
│   ├── index.html
│   ├── styles.css
│   └── js/
├── backend/            # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── routers/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   ├── seed_loader.py
│   └── init_admin.py
├── start.sh / start.bat
└── docker-compose.yml
```

## Environment variables

Kopieer `backend/.env.example` naar `backend/.env`:

```bash
SECRET_KEY=een-willekeurige-string-hier
DATABASE_PATH=stage_monitoring.db
FRONTEND_ORIGINS=http://localhost:8080
API_PORT=8001
```

## Belangrijke endpoints

| Domein | Endpoints |
|--------|-----------|
| Auth | `POST /auth/login`, `GET /auth/me` |
| Internships | `GET /internships`, `POST /internships` |
| Proposals | `PATCH /internships/{id}/proposal`, `POST /internships/{id}/resubmit` |
| Internship beheer | `PATCH /internships/{id}` (docent/mentor herToewijzen), `POST /internships/{id}/terminate` (stage stopzetten) |
| Agreements | `POST /internships/{id}/agreement`, `PATCH /internships/{id}/agreement` |
| Logbooks | `GET /internships/{id}/logbooks`, `POST /internships/{id}/logbooks` |
| Evaluations | `GET /internships/{id}/evaluations`, `POST /internships/{id}/evaluations` |
| Competencies | `GET /competencies`, `POST /competencies` |
| Dashboard | `GET /me/dashboard` |
| Users | `GET /users`, `GET /users/{id}` |

## Notes

- Statusovergangen in `app/services/lifecycle.py`
- Stage -> "Lopend" vereist gevalideerde overeenkomst
- PDFs in `uploads/agreements/`
- JWT vervalt na 24u
- SQLite default; pas `SQLALCHEMY_DATABASE_URL` in `app/database.py` aan voor PostgreSQL/MySQL
- Migraties via Alembic (`backend/alembic/README`)
- Audit logs in `audit_logs` tabel, raadpleegbaar via `GET /audit` (admin only)
