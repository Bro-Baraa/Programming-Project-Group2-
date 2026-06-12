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
python seed_loader.py    # uitgebreide testdata (YAML-backed)
# of: python seed.py      # alias voor hetzelfde
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
| Audit | `GET /audit` |
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
│   │   ├── audit.py
│   │   ├── me.py
│   │   └── reports.py
│   ├── schemas/             # Pydantic schemas per domein
│   └── services/            # Business logic
├── tests/                   # pytest suite
├── uploads/agreements/      # PDF uploads
├── init_admin.py            # Eerste setup
├── seed.py / seed_loader.py
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

## Audit Log

Alle belangrijke acties worden automatisch gelogd in de `audit_logs` tabel en zijn raadpleegbaar via `GET /audit` (enkel admin).

| Actie | Wanneer |
|---|---|
| `login` | Gebruiker logt in |
| `internship.create` | Student dient stage in |
| `proposal.submit` | Student dient voorstel in |
| `proposal.edit` | Student bewerkt voorstel |
| `proposal.resubmit` | Student herindient voorstel |
| `proposal.review` | Commissie beoordeelt voorstel |
| `proposal.withdraw` | Student trekt voorstel in |
| `agreement.upload` | Student uploadt overeenkomst |
| `agreement.validate` | Commissie/admin valideert overeenkomst |
| `logbook.create` | Student maakt logboek aan |
| `logbook.submit` | Student dient logboek definitief in |
| `logbook.validate` | Mentor valideert logboek |
| `evaluation.create` | Docent maakt evaluatie aan |
| `evaluation.finalize` | Docent finaliseert evaluatie |
| `competency.create` | Admin maakt competentie aan |
| `competency.update` | Admin wijzigt competentie |
| `competency.delete` | Admin verwijdert competentie |
| `competency.deactivate` | Admin deactiveert competentie |
| `user.create` | Admin maakt gebruiker aan |
| `user.update` | Admin wijzigt gebruiker |
| `user.delete` | Admin verwijdert gebruiker |

Nieuwe events toevoegen via `app/services/audit.py`:
```python
from app.services.audit import log_event
log_event(db, "mijn.actie", user=current_user, entity_type="internship", entity_id=id, detail="Omschrijving")
```
