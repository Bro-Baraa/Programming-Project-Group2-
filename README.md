# Stage Monitoring Tool

Stagevolgsysteem voor Toegepaste Informatica - Erasmus Hogeschool Brussel.

**Stack:** FastAPI + SQLite backend, vanilla HTML/CSS/JS frontend.
**Trello:** https://trello.com/b/aDORQ9Dz/projectgroep-2-wt
**Status:** Alle 31 user stories geimplementeerd - [detail](docs/progress-tracking/user-stories-overzicht.md)

---

## Demo

| Demo | Link |
|------|------|
| Installatie & opstarten | https://youtu.be/hzRFF7YV1s4 |
| Volledige rondleiding | https://youtu.be/Ul0cZwO2a4Q |
| Stagevoorstel indienen | https://youtu.be/-PMWk7rEaf4 |

---

## Installatie

**Vereisten:** Python 3.11+

```bash
# Aanbevolen (alles automatisch)
python3 start.py

# Handmatig
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed_loader.py
python -m uvicorn app.main:app --port 8001

# Docker
docker compose up
```

App bereikbaar op **http://localhost:8001** (http://localhost:8080 via Docker).

> `start.py` draait backend + statische frontend op één poort (8001). Wil je de frontend apart via de Vite dev-server (poort 8080), gebruik dan `./start.sh` — zie [installatiehandleiding §5](docs/Stage_Monitoring_Tool_Documentatie.md#5-installatie-handleiding).

---

## Testaccounts

Op het inlogscherm staat een knop "Test accounts laden" om in te loggen zonder wachtwoord.

| Rol | E-mail | Wachtwoord |
|-----|--------|------------|
| Admin | admin@school.be | demo123 |
| Student | student1@school.be | student123 |
| Commissie | commissie1@school.be | commissie123 |
| Docent | docent1@school.be | docent123 |
| Mentor | mentor1@school.be | mentor123 |

Meer accounts (10 studenten, 5 mentoren) in de [hoofddocumentatie](docs/Stage_Monitoring_Tool_Documentatie.md#6-testaccounts).

---

## Tests

```bash
cd backend && pytest
```

---

## Documentatie

| Document | Beschrijving |
|---|---|
| [Hoofddocumentatie](docs/Stage_Monitoring_Tool_Documentatie.md) | Volledige projectdocumentatie |
| [Testverslag](docs/testverslag.md) | 20 testcases, samenvatting per component |
| [User stories](docs/progress-tracking/user-stories-overzicht.md) | Status 31/31 met implementatiebewijs |
| [Feature TODO](docs/progress-tracking/feature-todo.md) | Acceptatiecriteria per feature |
| [Gap analyse](docs/gap-analyse.md) | Gepland vs. gerealiseerd |
| [Backend architectuur](docs/architectuur.md) | 5-lagenmodel, request flow |

---

Groep 2 - Juan Benjumea-Moreno, Baraa Alaswad, Yorick Steehout, Samy Bekkaoui, Leila Daif
