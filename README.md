# Stage Monitoring Tool

Stagevolgsysteem voor Toegepaste Informatica (Erasmus Hogeschool Brussel).

**Stack:** FastAPI + SQLite backend, HTML/JS frontend.

## Quick start

```bash
cd frontend && npm install
./start.sh
```

- Backend: http://localhost:8001
- Frontend: http://localhost:8080

### Eerste keer setup

```bash
cd backend
cp .env.example .env
python init_admin.py
```

### Testaccounts

| Rol | E-mail | Wachtwoord |
|-----|--------|------------|
| Admin | admin@school.be | demo123 |
| Student | student1@school.be | student123 |
| Commissie | commissie1@school.be | commissie123 |
| Docent | docent1@school.be | docent123 |
| Mentor | mentor1@school.be | mentor123 |

### Start opties

```bash
./start.sh              # backend + frontend
./start.sh --backend    # alleen backend
./start.sh --frontend   # alleen frontend
./start.sh --reset      # reset database + seed
./start.sh --help
```

### Handmatig starten

```bash
# Terminal 1
cd backend
uv run python -m uvicorn app.main:app --reload --port 8001

# Terminal 2
cd frontend
npm run dev
```

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
