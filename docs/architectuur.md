# Backend Architectuur - Stage Monitoring Tool

Dit document legt de structuur van de backend uit. Het is bedoeld voor medestudenten die meer aan de backend werken, maar ook voor zij die aan de frontend werken en willen begrijpen hoe de data en API's werken.

## Waarvoor dient de Backend?

Het is het "brein" van de applicatie dat:
- Data opslaat in een database (SQLite)
- Beveiligt wie wat mag zien en doen
- API's aanbiedt waar de frontend mee praat

Wij gebruiken **FastAPI** (een modern Python framework).

---

## De 5 Lagen van ons Systeem

Onze backend is opgebouwd uit 5 lagen. Elk laag heeft een specifieke taak:

### Laag 1: Database 
**Bestanden:** `models.py`, `database.py`

Dit is waar alle gegevens worden bewaard:
- Gebruikers (studenten, docenten, mentors, commissieleden, admins)
- Stages en hun status
- Bedrijven waar studenten stage lopen
- Logboeken, evaluaties, en feedback

**Belangrijke concept:** 
- Een **Internship** (stage) is het centrale object. Alles hangt eraan vast: het voorstel, de overeenkomst, logboeken, evaluaties.
- Relaties leggen vast wie wat mag zien (bijv. een student ziet alleen zijn eigen stages).

### Laag 2: Schema's
**Map:** `schemas/`

Schemas zorgen dat data die binnenkomt correct is voordat we ze verwerken. Ze valideren en checken bijvoorbeeld:
- Is het e-mailadres geldig?
- Zijn alle verplichte velden ingevuld?
- Kloppen de datums?

Ze zorgen ook dat we propere antwoorden terugsturen naar de frontend.

### Laag 3: Authenticatie
**Bestand:** `auth.py`

Dit systeem controleert wie er mag inloggen en wat ze mogen doen:
- Wachtwoorden worden veilig opgeslagen (gehasht)
- Ingelogde gebruikers krijgen een **JWT token** (een soort toegangsbewijs)
- Rollen bepalen de rechten: student, docent, commissie, mentor, of admin

**Veiligheidsprincipe:** 
Niet iedereen mag alles zien. Een student ziet alleen zijn eigen stages. Een docent ziet alleen de stages waarvoor hij verantwoordelijk is. Alleen commissieleden en admins zien alles.

### Laag 4: Routers
**Map:** `routers/`

Routers zijn de "deuren" van onze API. Ze luisteren naar verzoeken van de frontend:
- **Auth router:** Inloggen, registreren
- **Internships router:** Stages aanmaken en ophalen
- **Proposals router:** Voorstellen goedkeuren/afkeuren
- **Logbooks router:** Logboeken bijhouden
- **Evaluations router:** Evaluaties invullen
- **Competencies router:** Competenties beheren (admin)

Elke router werkt op een specifiek webadres (URL). Bijvoorbeeld: `/internships` voor alles rond stages.

### Laag 5: Services
**Map:** `services/`

Dit is waar de "slimme" logica zit. Als een actie meerdere stappen vereist of complexe regels heeft, staat dat hier:
- Het evalueren van een voorstel (met statuswijzigingen)
- Het berekenen van gewogen evaluatiescores
- Het controleren of iemand toegang heeft tot een specifieke stage

**Waarom apart?**
Zo kunnen we complexe logica testen en hergebruiken zonder het in de routers te moeten kopiëren.

---

## Hoe Werkt een Verzoek?

Stel: een student wil een nieuwe stage indienen. Dit gebeurt stap voor stap:

1. **Frontend stuurt data** naar `/internships` met alle gegevens (bedrijf, periode, omschrijving)

2. **Schema valideert:** Is alles ingevuld? Klopt de email?

3. **Authenticatie controleert:** Is de gebruiker ingelogd? Is het een student?

4. **Router verwerkt:** 
   - Maakt een bedrijfrecord aan
   - Maakt een stage-record aan (gekoppeld aan het bedrijf en de student)
   - Maakt een voorstelrecord aan
   - Slaat alles op in de database

5. **Schema maakt antwoord:** Het nieuwe stage-object wordt omgezet naar JSON en teruggestuurd

---

## Beveiliging in Lagen

We gebruiken "Defense in Depth" - meerdere beveiligingslagen:

| Laag | Wat doet het? |
|------|---------------|
| **CORS** | Alleen toegestane websites mogen de API gebruiken (localhost tijdens ontwikkeling) |
| **JWT Token** | Gebruikers bewijzen hun identiteit met een tijdelijk toegangsbewijs |
| **Rol-check** | Endpoints controleren of je de juiste rol hebt (student, docent, etc.) |
| **Resource-check** | Bij specifieke stages wordt gekeken: is deze van jou? Ben je de mentor? |
| **Input-validatie** | Alle binnenkomende data wordt gecontroleerd op type en verplichte velden |
| **Status-validatie** | Status-wijzigingen (bijv. van "Ingediend" naar "Goedgekeurd") worden gecontroleerd |

---

## De Belangrijkste Onderdelen

### Gebruikers en Rollen

Er zijn 5 soorten gebruikers:

- **Student:** Dient stages in, vult logboeken in, ziet eigen evaluaties
- **Docent:** Beoordeelt stages, geeft evaluaties, volgt studenten op
- **Commissielid:** Beoordeelt voorstellen, geeft feedback, ziet overzichten
- **Mentor (bedrijf):** Kijkt logboeken na, valideert aanwezigheid
- **Admin:** Beheert competenties, kan alles zien

### Stage workflow:

Een stage doorloopt verschillende fasen:

1. **Ingediend** → Student dient voorstel in
2. **In Beoordeling** → Commissie bekijkt het
3. **Goedgekeurd** / **Afgekeurd** / **Aanpassingen Vereist**
4. **Overeenkomst Ingediend** → Student uploadt ondertekende overeenkomst
5. **Lopend** → Stage is actief
6. **Afgerond** → Stage is klaar, evaluaties definitief

### Kernentiteit: de Stage 

De Stage is het middelpunt. Alles hangt eraan vast:
- Het heeft één **voorstel** (proposal)
- Het heeft één **overeenkomst** (agreement) als PDF
- Het heeft meerdere **logboeken** (wekelijks)
- Het heeft evaluaties (tussentijds en finaal)
- Het is gekoppeld aan een student, docent, mentor, en bedrijf

---

## Werkwijze: Hoe Bouwen We Dit?

### 1. Een nieuw endpoint toevoegen

Als je een nieuwe functie bouwt:
1. Kijk in welke router het past (bijv. logboeken in `logbooks.py`)
2. Definieer het schema in `schemas/` (wat komt binnen, wat gaat uit)
3. Voeg de functie toe aan de router met juiste dependencies
4. Schrijf de logica (direct in router als simpel, anders in `services/`)
5. Test met een pytest test

### 2. Een nieuwe entiteit toevoegen

Als je een nieuw soort data nodig hebt:
1. Voeg model toe aan `models.py` (SQLAlchemy)
2. Voeg schema's toe aan `schemas/` (Pydantic)
3. Maak router in `routers/` met CRUD operaties
4. Importeer router in `main.py`

### 3. Beveiliging toevoegen

Altijd controleren:
- Is de gebruiker ingelogd? (Depends `get_current_active_user`)
- Heeft hij de juiste rol? (Depends `require_student`, etc.)
- Mag hij deze specifieke resource zien? (Service functie `can_access_internship`)

---

## API Overzicht (voor Frontend Developers)

### Authenticatie
- `POST /auth/login` - Inloggen
- `POST /auth/register` - Nieuwe gebruiker (alleen admin)
- `GET /auth/me` - Wie ben ik?

### Stages
- `GET /internships` - Lijst (automatisch gefilterd per rol)
- `POST /internships` - Nieuwe stage
- `GET /internships/{id}` - Details
- `PATCH /internships/{id}` - Wijzigen (staff only)

### Voorstellen
- `GET /internships/{id}/proposal` - Zien
- `PATCH /internships/{id}/proposal` - Beoordelen (commissie)

### Overeenkomsten
- `POST /internships/{id}/agreement` - Upload PDF

### Logboeken
- `GET /internships/{id}/logbooks` - Wekelijkse logboeken
- `POST /internships/{id}/logbooks` - Nieuw logboek

### Evaluaties
- `GET /internships/{id}/evaluations` - Lijst
- `POST /internships/{id}/evaluations` - Start evaluatie (docent)
- `PATCH .../rules/{id}` - Score invoeren
- `POST .../finalize` - Afronden

### Competenties (Admin)
- `GET /competencies` - Lijst
- `POST /competencies` - Toevoegen
- `DELETE /competencies/{id}` - Verwijderen

### Rapporten
- `GET /internships/stats/dashboard` - Dashboard cijfers
- `GET /internships/reports/final` - Eindrapporten

---

## Belangrijke Principes voor Dit Project

1. **Duidelijke scheiding:** Database, logica, en API endpoints zitten apart
2. **Veiligheid eerst:** Altijd checken wie wat mag
3. **Student-gericht:** Alles draait om de stage en de voortgang
4. **Eenvoud:** SQLite is bewust gekozen voor eenvoud, geen complexe server nodig
5. **Nederlandse terminologie:** Statussen en termen zijn in het Nederlands voor duidelijkheid

---

## Tips voor het Werken met de Code

- **Testen:** Gebruik `pytest` en kijk naar bestaande tests als voorbeeld
- **Database wijzigingen:** SQLite maakt tabellen automatisch, maar bestaande data gaat niet verloren bij kleine wijzigingen
- **Foutmeldingen:** Gebruik HTTPException met duidelijke meldingen
- **Logging:** Gebruik console.warn alleen voor onverwachte situaties, niet voor normale flow
- **Documentatie:** Houd deze documentatie bij als je de structuur wijzigt