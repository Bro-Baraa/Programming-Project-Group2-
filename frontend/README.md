# Stage Monitoring Tool — Frontend

HTML/CSS/JS frontend met API-integratie naar de FastAPI backend.

## Snel Starten

```bash
cd frontend
python3 -m http.server 8080
```

Ga naar **http://localhost:8080**

De backend moet draaien op `http://localhost:8001`.

## 📁 Bestanden

| Bestand | Beschrijving |
|---------|-------------|
| `index.html` | Hoofdpagina met alle UI-templates |
| `app.js` | Kernlogica: views, formulieren, API-communicatie |
| `api-client.js` | Herbruikbare API-client (Auth, Internships, Evaluations, ...) |
| `styles.css` | Gedeelde stijlen |

Oude versies staan in `prototype/`:
- `index-original.html` + `app-original.js` — eerste prototype (geen backend)
- `index-improved-localstorage.html` + `app-improved-localstorage.js` — localStorage-versie

## Authenticatie

Inloggen met JWT-token. Testaccounts:

| Rol | E-mail | Wachtwoord |
|-----|--------|------------|
| Admin | admin@school.be | admin123 |
| Student | student1@school.be | student123 |
| Commissie | commissie1@school.be | commissie123 |
| Docent | docent1@school.be | docent123 |
| Mentor | mentor1@school.be | mentor123 |

## Rollen & Schermen

| Rol | Schermen |
|-----|----------|
| **Student** | Dashboard, Stagevoorstel indienen, Logboek invullen, Overeenkomst uploaden, Evaluaties bekijken |
| **Stagecommissie** | Voorstellen beoordelen (goedkeuren/afkeuren/aanpassingen), Overzicht met statistieken |
| **Docent** | Logboeken opvolgen, Feedback geven, Evaluaties invullen (scores per competentie) |
| **Stagementor** | Logboeken valideren (aftekenen) |
| **Administratie** | Competentiebeheer + gewichten |

## API-Integratie

Alle data komt van de FastAPI-backend:
- `GET /me/dashboard` — alles voor de dashboard-view
- `GET /internships` — stages (met zoeken, filteren, paginatie)
- `POST /internships` — voorstel indienen
- `PATCH /internships/{id}/proposal` — goedkeuren/afkeuren
- `GET /internships/{id}/logbooks` — logboeken
- `POST /internships/{id}/evaluations` — evaluatie aanmaken
- `PATCH /evaluations/{id}/rules/{rule_id}` — scores invoeren
- `POST /evaluations/{id}/finalize` — evaluatie afronden
- `GET /internships/{id}/agreement/download` — PDF downloaden

Zie Swagger-docs op http://localhost:8001/docs

## Demo Happy Path

1. **Student** logt in → indient voorstel
2. **Commissie** logt in → selecteert voorstel → klikt "Goedkeuren"
3. **Student** logt in → uploadt overeenkomst (PDF)
4. **Commissie** logt in → valideert overeenkomst → status wordt "Lopend"
5. **Student** logt in → vult logboek in (week 1)
6. **Mentor** logt in → selecteert stage → klikt "Valideren" op logboek
7. **Docent** logt in → selecteert stage → maakt evaluatie → geeft scores → slaat op