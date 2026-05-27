# Stage Monitoring Tool - Backend

FastAPI + SQLite backend.

## Quick Start

```bash
cd backend
pip install -r requirements.txt        # or: uv pip install -r requirements.txt
cp .env.example .env
python init_admin.py                   # maakt database + admin user
uvicorn app.main:app --reload
```

API: `http://localhost:8001`  
Docs: `http://localhost:8001/docs`

### Testdata seeden

```bash
python seed.py           # basis users + competenties
# of
python seed_complete.py  # uitgebreidere testdata
```

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
| Dashboard | `GET /me/dashboard`, `GET /internships/stats/dashboard` |
| Users | `GET /users`, `GET /users/{id}` |

Zie `/docs` voor de volledige lijst.

## Projectstructuur

```
backend/
├── app/
│   ├── main.py              # FastAPI entrypoint
│   ├── database.py          # SQLAlchemy + SQLite
│   ├── models.py            # ORM modellen
│   ├── auth.py              # JWT + wachtwoord hashing
│   ├── dependencies.py      # Gedeelde dependencies
│   ├── routers/             # API endpoints per domein
│   │   ├── auth.py
│   │   ├── internships.py
│   │   ├── proposals.py
│   │   ├── agreements.py
│   │   ├── logbooks.py
│   │   ├── evaluations.py
│   │   ├── competencies*.py
│   │   ├── feedback.py
│   │   ├── users.py
│   │   ├── me.py
│   │   └── reports.py
│   ├── schemas/             # Pydantic schemas per domein
│   └── services/            # Business logic
├── tests/                   # pytest suite
├── uploads/agreements/      # PDF uploads
├── init_admin.py            # Eerste setup
├── seed.py / seed_complete.py
├── requirements.txt
└── pytest.ini
```

## Database

SQLite by default (geen setup nodig). Wil je PostgreSQL/MySQL: pas `SQLALCHEMY_DATABASE_URL` in `app/database.py` aan.

## Environment Variables

```bash
cp .env.example .env
```

Minimaal nodig:
```
SECRET_KEY=een-willekeurige-string-hier
```

## Testen

```bash
pytest
```

## Notes

- Statusovergangen worden gevalideerd in `app/services/lifecycle.py` (`_TRANSITIONS`)
- Een stage kan pas naar "Lopend" als de overeenkomst is gevalideerd
- PDFs worden opgeslagen in `uploads/agreements/`
- JWT tokens verlopen na 24 uur