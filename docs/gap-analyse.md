# Gap Analyse - Stage Monitoring Tool

Groep 2 - Toegepaste Informatica
Erasmus Hogeschool Brussel
Academiejaar 2025-2026

Een overzicht van wat gepland was vs. wat gerealiseerd is.

---

## Afwijkingen t.o.v. de initiele analyse

| Onderdeel | Initiele analyse | Uiteindelijke keuze | Reden |
|---|---|---|---|
| Frontend framework | React + Tailwind | Vanilla HTML/CSS/JS + Vite | Eenvoudiger, geen framework overhead, snellere ontwikkeling |
| Backend framework | FastAPI (REST) | FastAPI (REST) | Zoals gepland |
| Database | SQLite | SQLite + SQLAlchemy ORM | Zoals gepland; ORM toegevoegd voor structuur |
| Notificaties | E-mail service | In-app notificaties (polling) | E-mail was te complex voor scope |
| Auth | JWT (access/refresh) | JWT access token (24u) | Refresh tokens niet nodig |
| Rollen | 6 rollen (Admin + Administratie apart) | 5 rollen (samengevoegd) | Vereenvoudiging zonder functieverlies |
| Datamodel | 11 tabellen | 14 tabellen | Extra voor audit, notificaties, feedback, versiegeschiedenis |

Belangrijkste afwijking: vanilla JS ipv React. Dit volstond voor de functionaliteit en vermeed de leercurve van een framework. Overige afwijkingen zijn vereenvoudigingen (auth, rollen) of uitbreidingen (datamodel).

---

## Sprintplanning: gepland vs. gerealiseerd

| Sprint | Focus | Gerealiseerd? |
|---|---|---|
| Sprint 1 | Gebruikersbeheer + stagevoorstellen (indienen, beoordelen, feedback) | Ja, volledig |
| Sprint 2 | Overeenkomst uploaden + wekelijks logboekbeheer | Ja, volledig |
| Sprint 3 | Evaluaties + competenties: gewichten, feedback, tussentijdse/finale evaluaties | Ja, volledig |
| Sprint 4 | Meldingen, rapportage, export, afwerking | Ja, volledig |

---

## Reflectie

**Wat goed ging:**
- Alle 31 user stories geimplementeerd (back-end + frontend)
- Gelaagde architectuur: overzichtelijk en onderhoudbaar
- Tests gaven vertrouwen bij refactoring
- Docker + Fly.io voor werkende demo
- Flexibel competentieprofiel-systeem met versiebeheer

**Mogelijke verbeteringen:**
- E-mailnotificaties naast in-app
- WebSocket i.p.v. polling voor real-time notificaties
- Actieve Alembic migraties
- PostgreSQL voor productie
- Verder optimaliseren van accessibility

---

## Gebruikte tools

| Tool | Gebruik |
|---|---|
| GitHub | Versiebeheer, pull requests, code reviews |
| Trello | Taakopvolging (To Do, Bezig, Review, Klaar) |
| Teams | Communicatie |
| Docker + Fly.io | Containerisatie + cloud hosting |
| Vite | Frontend dev server |
| pytest | Backend testing |
