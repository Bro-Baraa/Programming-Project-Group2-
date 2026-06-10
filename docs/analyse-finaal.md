# Finale Analyse - Stage Monitoring Tool

**Groep 2 - Toegepaste Informatica**
Erasmus Hogeschool Brussel
Academiejaar 2025-2026

---

## 1. Probleembeschrijving

### 1.1 Aanleiding

Het stageproces binnen de opleiding Toegepaste Informatica verliep tot nu toe versnipperd en grotendeels handmatig. Gegevens en documenten zaten verspreid over e-mail, Excel en losse formulieren. Dit leidde tot een aantal concrete problemen:

- Documenten zoals stageovereenkomsten raakten soms kwijt of werden te laat ingediend.
- Er was geen centraal overzicht van waar een stage zich bevond in het proces.
- Communicatie tussen student, commissie, docent en mentor kostte veel manuele opvolging.
- Aanpassingen aan evaluatiecriteria vereisten telkens codewijzigingen.

### 1.2 Doelstelling

Het doel van dit project was een webapplicatie bouwen die het volledige stageproces centraliseert: van het indienen van een voorstel tot de finale evaluatie. Alle betrokken partijen (student, stagecommissie, docent, stagementor en administratie) moesten op een centrale plek hun taken kunnen uitvoeren en de status van elke stage kunnen raadplegen.

De vijf kerndoelstellingen waren:

| # | Doelstelling | Concreet effect |
|---|---|---|
| 1 | Centralisatie | Alle stagegegevens op een platform met dossierhistoriek |
| 2 | Transparantie | Voor elke rol een helder statusoverzicht per stage |
| 3 | Efficientie | Automatische notificaties en validatieflows in plaats van ad-hoc mails |
| 4 | Wendbaarheid | Competenties en gewichten configureerbaar zonder deploy |
| 5 | Traceerbaarheid | Audit trail van beslissingen, uploads en evaluaties |

---

## 2. Functionele Analyse

### 2.1 Gebruikersrollen

De applicatie ondersteunt vijf rollen, elk met eigen verantwoordelijkheden:

| Rol | Kernverantwoordelijkheden |
|---|---|
| **Student** | Stage aanvragen, overeenkomst uploaden, logboeken invullen, zelfevaluatie beschrijven, eindresultaat raadplegen |
| **Stagecommissie** | Voorstellen beoordelen (goedkeuren, afkeuren, aanpassingen vragen), feedback geven, overeenkomsten valideren |
| **Docent** | Logboeken opvolgen, tussentijdse en finale evaluaties invullen, feedback per competentie, eindrapport genereren |
| **Stagementor** | Wekelijkse logboeken aftekenen, feedback per competentie geven |
| **Admin/Administratie** | Gebruikersbeheer, competentieprofielen en gewichten beheren, rapportages exporteren |

### 2.2 Rollenmatrix (CRUD per procesdeel)

| Rol | Aanvraag | Beoordeling | Overeenkomst | Logboeken | Evaluatie | Configuratie |
|---|---|---|---|---|---|---|
| Student | Create/Read | Read | Upload/Read | Create/Read | Read | - |
| Stagecommissie | Read | Update | Read/Validate | Read | Read | - |
| Docent | Read | Read | Read | Read/Comment | Create/Update | - |
| Stagementor | Read | Read | Read | Read/Verify | Create/Update | - |
| Admin | Read | Read | Read | Read | Read | Full CRUD |

### 2.3 Procesfasen

Het stageproces doorloopt vijf opeenvolgende fasen:

| Fase | Actor(en) | Output |
|---|---|---|
| 1. Aanvraag | Student | Stagevoorstel met status "Ingediend" |
| 2. Beoordeling | Stagecommissie | Status: Goedgekeurd, Afgekeurd, of Aanpassingen Vereist |
| 3. Overeenkomst | Student + Commissie/Admin | Overeenkomst ingediend en gevalideerd |
| 4. Opvolging | Student + Docent + Mentor | Wekelijkse logboeken en feedback |
| 5. Evaluatie | Docent + Mentor | Tussentijdse/finale evaluatie en eindrapport |

### 2.4 Statusmodel (state machine)

Een stage doorloopt de volgende statussen:

```
Ingediend -> In Beoordeling -> Goedgekeurd -> Overeenkomst Ingediend -> Lopend -> Afgerond
                             -> Afgekeurd
                             -> Aanpassingen Vereist -> (opnieuw) Ingediend
```

Kritische business rules:

- Alleen de stagecommissie mag de voorstelstatus wijzigen tijdens beoordeling.
- Overgang naar "Lopend" kan alleen als de overeenkomst gevalideerd is.
- Bij "Aanpassingen Vereist" is feedback verplicht.
- Een finale evaluatie is na afronding niet meer wijzigbaar.
- Alle statuswijzigingen worden gelogd in de audit trail (tijdstip + actor).

### 2.5 User Stories

Alle 29 user stories zijn geimplementeerd. Hieronder het volledige overzicht:

| ID | User story | Fase | Status |
|---|---|---|---|
| US-01 | Als student wil ik een stagevoorstel indienen met bedrijfs- en opdrachtgegevens zodat de stagecommissie kan beoordelen. | Aanvraag | OK |
| US-02 | Als student wil ik de status van mijn stagevoorstel bekijken zodat ik de voortgang ken. | Beoordeling | OK |
| US-03 | Als student wil ik feedback ontvangen bij afkeuring of aanpassingen zodat ik mijn voorstel kan verbeteren. | Beoordeling | OK |
| US-04 | Als student wil ik een stageovereenkomst uploaden zodat administratie en verzekering in orde zijn. | Overeenkomst | OK |
| US-05 | Als student wil ik wekelijks een logboek invullen met taken en reflecties zodat docent en mentor mijn voortgang volgen. | Opvolging | OK |
| US-06 | Als student wil ik per competentie beschrijven wat ik geleerd heb zodat ik voortgang kan aantonen. | Opvolging | OK |
| US-07 | Als student wil ik feedback van docent/mentor lezen zodat ik gericht kan bijsturen. | Opvolging | OK |
| US-08 | Als student wil ik een historiek van mijn logboeken zien zodat ik mijn evolutie kan opvolgen. | Opvolging | OK |
| US-09 | Als student wil ik mijn eindevaluatierapport raadplegen zodat ik mijn finale beoordeling ken. | Evaluatie | OK |
| US-10 | Als stagecommissielid wil ik een lijst van voorstellen zien zodat ik kan beoordelen. | Aanvraag | OK |
| US-11 | Als stagecommissielid wil ik voorstellen goedkeuren, afkeuren of aanpassingen vragen zodat kwaliteit gewaarborgd blijft. | Beoordeling | OK |
| US-12 | Als stagecommissielid wil ik feedback meegeven bij beslissingen zodat de student weet wat te wijzigen. | Beoordeling | OK |
| US-13 | Als stagecommissielid wil ik controleren of de overeenkomst is opgeladen zodat verzekering gegarandeerd is. | Overeenkomst | OK |
| US-14 | Als stagecommissielid wil ik overzicht van alle stages en statussen zodat het proces monitorbaar blijft. | Opvolging | OK |
| US-15 | Als docent wil ik wekelijkse logboeken inzien en opvolgen zodat ik gericht kan coachen. | Opvolging | OK |
| US-16 | Als docent wil ik feedback per competentie geven zodat studenten weten waar ze staan. | Opvolging | OK |
| US-17 | Als docent wil ik een tussentijdse evaluatie registreren zodat problemen vroeg opgemerkt worden. | Opvolging | OK |
| US-18 | Als docent wil ik de finale evaluatie invullen met score per competentie zodat de eindbeoordeling correct is. | Evaluatie | OK |
| US-19 | Als docent wil ik een eindoverzicht per student genereren zodat administratie kan rapporteren. | Evaluatie | OK |
| US-20 | Als docent wil ik notificatie ontvangen bij nieuwe logboeken zodat ik tijdig reageer. | Opvolging | OK |
| US-21 | Als stagementor wil ik wekelijks logboeken inkijken zodat ik voortgang valideer. | Opvolging | OK |
| US-22 | Als stagementor wil ik logboeken aftekenen zodat opvolging aantoonbaar is. | Opvolging | OK |
| US-23 | Als stagementor wil ik feedback per competentie geven zodat de evaluatie volledig is. | Evaluatie | OK |
| US-24 | Als stagementor wil ik overzicht van stagecontext zien zodat ik goede begeleiding kan geven. | Aanvraag | OK |
| US-25 | Als administratie wil ik competenties en gewichten beheren zonder codewijzigingen zodat de evaluatie altijd up-to-date is met het beleid. | Evaluatie | OK |
| US-26 | Als administratie wil ik zien welke studenten hun overeenkomst al hebben ingediend zodat ik kan opvolgen of alle papieren in orde zijn. | Overeenkomst | OK |
| US-27 | Als administratie wil ik gebruikers beheren zodat alleen de juiste mensen toegang hebben. | Alle | OK |
| US-28 | Als administratie wil ik rapportages exporteren zodat data bruikbaar is voor rapportering. | Evaluatie | OK |
| US-29 | Als gebruiker wil ik een melding krijgen als er iets verandert dat mij aangaat zodat ik altijd op de hoogte ben. | Alle | OK |

### 2.6 Acceptatiecriteria (selectie van de belangrijkste)

**US-01 - Stagevoorstel indienen**
- Formulier valideert verplichte velden (student, bedrijf, docent, opdracht, periode).
- Na indienen krijgt het dossier status "Ingediend".
- Student krijgt bevestiging; commissie krijgt notificatie.

**US-05 - Wekelijks logboek**
- Per student maximaal een logboek per weeknummer.
- Opslaan als concept of definitief indienen.
- Na indiening zichtbaar voor docent en mentor.
- Niet-ingevulde weken gemarkeerd als "Ontbrekend".

**US-11 - Beoordeling voorstel**
- Drie beslissingen mogelijk: Goedgekeurd, Afgekeurd, Aanpassingen Vereist.
- Bij "Aanpassingen Vereist" is feedback verplicht.
- Student krijgt notificatie bij elke statuswijziging.

**US-18 - Finale evaluatie**
- Score per actieve competentie (schaal 1-5).
- Gewogen eindscore wordt automatisch berekend.
- Na afronding geen wijzigingen meer mogelijk.

**US-25 - Competenties beheren**
- Competentie bevat naam, beschrijving, gewicht en actief-status.
- Validatie: som gewichten = 100%.
- Wijzigingen gelden enkel voor nieuwe stages; historische evaluaties blijven ongewijzigd.

---

## 3. Technische Architectuur

### 3.1 Overzicht

De applicatie is opgebouwd als een client-server architectuur met een gescheiden frontend en backend die via een REST API communiceren.

| Laag | Technologie | Motivatie |
|---|---|---|
| **Frontend** | HTML/CSS/JavaScript (vanilla) + Vite dev server | Lichtgewicht, geen framework overhead, snelle ontwikkeling |
| **Backend API** | Python FastAPI | Modern, snel, automatische API-documentatie, goede validatie via Pydantic |
| **Database** | SQLite + SQLAlchemy ORM | Geen server-setup nodig, eenvoudige deployment, voldoende voor dit project |
| **Authenticatie** | JWT (JSON Web Tokens) | Stateless sessiebeveiliging, rolgebaseerde toegang |
| **Deployment** | Docker + Fly.io | Eenvoudige containerisatie, gratis hosting voor demo |

### 3.2 Backend-architectuur (gelaagd)

De backend is opgebouwd uit vijf lagen, elk met een specifieke verantwoordelijkheid:

**Laag 1: Database (`models.py`, `database.py`)**
SQLAlchemy modellen definieren de databasestructuur. SQLite wordt als database gebruikt. Tabellen worden automatisch aangemaakt bij eerste opstart.

**Laag 2: Schema's (`schemas/`)**
Pydantic modellen valideren binnenkomende data (request) en formatteren uitgaande data (response). Ze controleren verplichte velden, e-mailformaten, datums, enzovoort.

**Laag 3: Authenticatie (`auth.py`)**
JWT-gebaseerde authenticatie met bcrypt-gehashte wachtwoorden. Rolgebaseerde autorisatie via dependency injection (`require_student`, `require_teacher`, `require_any_staff`, etc.).

**Laag 4: Routers (`routers/`)**
API endpoints per domein. Elke router behandelt een specifiek deel van de applicatie:

| Router | Verantwoordelijkheid |
|---|---|
| `auth.py` | Inloggen, registreren, huidige gebruiker ophalen |
| `internships.py` | Stages aanmaken, ophalen, wijzigen |
| `proposals.py` | Voorstel beoordelen, versiegeschiedenis |
| `agreements.py` | Overeenkomst uploaden, valideren |
| `logbooks.py` | Logboeken aanmaken, indienen, mentor-validatie |
| `evaluations.py` | Evaluaties starten, scores invullen, afronden |
| `competencies.py` | Competentieprofielen en items beheren |
| `feedback.py` | Feedback sturen en ophalen |
| `notifications.py` | Notificaties ophalen, markeren als gelezen |
| `reports.py` | Eindrapporten, CSV-export, PDF-generatie |
| `users.py` | Gebruikersbeheer (CRUD, admin only) |
| `audit.py` | Audit logs raadplegen (admin only) |

**Laag 5: Services (`services/`)**
Complexe business logica die door meerdere routers gebruikt wordt:

| Service | Verantwoordelijkheid |
|---|---|
| `lifecycle.py` | Statusovergangen van stages, voorstelverwerking, herindiening |
| `dashboard.py` | Dashboard-aggregatie met alerts en statistieken |
| `evaluations.py` | Evaluatielogica en gewogen scoreberekening |
| `notifications.py` | Notificatie-helper (`notify()`) |
| `audit.py` | Audit logging (`log_event()`) |
| `report_final.py` | Eindrapportgeneratie |
| `report_pdf.py` | PDF-export van eindrapporten |
| `logbooks.py` | Logboekvalidatie en weekberekening |

### 3.3 Frontend-architectuur

De frontend is een single-page applicatie gebouwd met vanilla HTML, CSS en JavaScript, zonder framework. De structuur:

| Bestand | Verantwoordelijkheid |
|---|---|
| `index.html` | Hoofdpagina met alle HTML-templates per rol |
| `js/app.js` | Kernlogica: view routing, formulierverwerking |
| `js/api-client.js` | Herbruikbare API-client modules voor alle endpoints |
| `js/ui-helpers.js` | UI utility functies (modals, toasts, formattering) |
| `js/notifications.js` | Notificatie bell met auto-polling (30s interval) |
| `js/views/student.js` | Student dashboard, voorstelformulier, logboeken, zelfevaluatie |
| `js/views/teacher.js` | Docent dashboard, logboekoverzicht, evaluaties |
| `js/views/mentor.js` | Mentor dashboard, logboekvalidatie |
| `js/views/committee.js` | Commissie dashboard, voorstelbeoordeling, overeenkomsten |
| `js/views/admin.js` | Admin dashboard, gebruikersbeheer, competentiebeheer, rapportages |
| `styles.css` | Volledige styling inclusief responsieve layout |

De frontend communiceert met de backend via de Vite dev server proxy (in development) of wordt direct geserveerd door de backend (in productie).

### 3.4 Beveiliging

We passen "Defense in Depth" toe met meerdere beveiligingslagen:

| Laag | Werking |
|---|---|
| **CORS** | Alleen toegestane origins mogen de API benaderen |
| **JWT Token** | Gebruikers authenticeren zich met een tijdelijk token (24u geldig) |
| **Wachtwoord hashing** | bcrypt hashing via passlib |
| **Rol-check** | Endpoints controleren de gebruikersrol via FastAPI dependencies |
| **Resource-check** | Bij specifieke stages wordt gecontroleerd of de gebruiker toegang heeft |
| **Input-validatie** | Alle binnenkomende data wordt gevalideerd via Pydantic schema's |
| **Status-validatie** | Statusovergangen worden afgedwongen in `lifecycle.py` |
| **Rate limiting** | Login, registratie en health endpoints: max. 10 requests/minuut per IP |
| **Productie-hardening** | Swagger UI en OpenAPI schema uitgeschakeld; `robots.txt` blokkeert crawlers |

---

## 4. Datamodel

### 4.1 Entiteiten

Het systeem bevat de volgende kerntabellen:

| Tabel | Beschrijving | Belangrijkste velden |
|---|---|---|
| `users` | Alle gebruikers van het systeem | id, email (unique), password_hash, role, first_name, last_name, is_active |
| `companies` | Bedrijven waar studenten stage lopen | id, name, address, sector, contact_person, contact_email, mentor_id |
| `internships` | Centrale entiteit: de stage | id, student_id, teacher_id, mentor_id, company_id, competency_profile_id, start_date, end_date, status |
| `proposals` | Stagevoorstellen (1-op-1 met stage) | id, internship_id, description, status, feedback, version, revision_count |
| `proposal_versions` | Versiegeschiedenis van voorstellen | id, proposal_id, version, description, status, feedback |
| `agreements` | Stageovereenkomsten (1-op-1 met stage) | id, internship_id, file_path, insurance_verified, status |
| `documents` | Overige documenten bij een stage | id, internship_id, doc_type, file_path |
| `logbooks` | Wekelijkse logboeken | id, internship_id, week_number, tasks, reflection, issues, status, mentor_validated |
| `competency_profiles` | Competentieprofielen per academiejaar | id, name, version, academic_year, active |
| `competencies` | Individuele competenties binnen een profiel | id, profile_id, name, description, weight, active |
| `evaluations` | Evaluaties (tussentijds of finaal) | id, internship_id, evaluator_id, eval_type, status, finalized |
| `evaluation_rules` | Score per competentie per evaluatie | id, evaluation_id, competency_id, score, student_description, evaluator_feedback |
| `notifications` | In-app notificaties | id, user_id, message, internship_id, link_view, is_read |
| `feedbacks` | Feedback tussen gebruikers | id, internship_id, from_user_id, to_user_id, message |
| `audit_logs` | Audit trail van alle acties | id, timestamp, user_id, user_email, action, entity_type, entity_id, detail |

### 4.2 Relaties

- Een **stage** is het centrale object. Alles hangt eraan vast.
- Een user (student) kan meerdere stages hebben.
- Een stage heeft precies een voorstel en maximaal een overeenkomst.
- Een stage heeft meerdere logboeken (een per week).
- Een stage kan meerdere evaluaties hebben (tussentijds + finaal).
- Een evaluatie bevat meerdere evaluation_rules (een per competentie).
- Een competentieprofiel bevat meerdere competenties.
- Bij aanmaak van een stage wordt het actieve competentieprofiel gekopieerd (via `competency_profile_id`), zodat historische stages ongewijzigd blijven bij profielwijzigingen.

### 4.3 Constraints

- `users.email` is uniek.
- `logbooks.week_number` in bereik 1-52.
- `evaluation_rules.score` in bereik 1-5.
- `competencies.weight` in bereik 0-100.
- Per actief profiel: som van alle competentiegewichten = 100%.

### 4.4 ER-diagram (vereenvoudigd)

```
USERS ||--o{ INTERNSHIPS : "student"
USERS ||--o{ INTERNSHIPS : "docent"
USERS ||--o{ INTERNSHIPS : "mentor"
COMPANIES ||--o{ INTERNSHIPS : "heeft"
INTERNSHIPS ||--|| PROPOSALS : "heeft"
INTERNSHIPS ||--o| AGREEMENTS : "heeft"
INTERNSHIPS ||--o{ LOGBOOKS : "heeft"
INTERNSHIPS ||--o{ EVALUATIONS : "heeft"
INTERNSHIPS ||--o{ FEEDBACKS : "heeft"
COMPETENCY_PROFILES ||--o{ COMPETENCIES : "definieert"
EVALUATIONS ||--o{ EVALUATION_RULES : "bevat"
COMPETENCIES ||--o{ EVALUATION_RULES : "gebruikt"
PROPOSALS ||--o{ PROPOSAL_VERSIONS : "historiek"
USERS ||--o{ NOTIFICATIONS : "ontvangt"
USERS ||--o{ AUDIT_LOGS : "acties"
```

---

## 5. Gerealiseerde Functionaliteiten

### 5.1 Stagevoorstel en beoordelingsflow

- Student vult een formulier in met bedrijfsgegevens, opdracht, periode en selecteert een docent en mentor.
- Het voorstel wordt opgeslagen met status "Ingediend". Commissieleden ontvangen een notificatie.
- De commissie kan het voorstel eerst "In Beoordeling" zetten en daarna een beslissing nemen (twee-staps flow).
- Bij "Aanpassingen Vereist" kan de student het voorstel bewerken en opnieuw indienen.
- Volledige versiegeschiedenis wordt bijgehouden in de `proposal_versions` tabel.

### 5.2 Overeenkomstbeheer

- Na goedkeuring kan de student een PDF-overeenkomst uploaden.
- Content-type validatie zorgt ervoor dat alleen PDF-bestanden geaccepteerd worden.
- Commissieleden kunnen de overeenkomst downloaden, de verzekeringsstatus controleren en valideren of markeren als "Onvolledig".
- Administratie heeft een overzichtstabel met alle overeenkomsten en hun status.

### 5.3 Logboeken

- Studenten vullen wekelijks een logboek in met taken, reflecties en problemen.
- Logboeken kunnen opgeslagen worden als concept of definitief ingediend.
- Bij indiening worden docent en mentor genotificeerd.
- Mentoren kunnen logboeken valideren (aftekenen).
- Ontbrekende weken worden automatisch berekend en visueel gemarkeerd als "Ontbrekend" (rode markering in de UI).

### 5.4 Evaluatiesysteem

- Docenten en mentoren kunnen tussentijdse en finale evaluaties aanmaken.
- Per evaluatie wordt voor elke competentie (uit het gekoppelde profiel) een score ingevuld.
- Studenten kunnen per competentie hun eigen vorderingen beschrijven (zelfevaluatie).
- De gewogen eindscore wordt automatisch berekend op basis van de competentiegewichten.
- Na afronding ("finalize") kan een evaluatie niet meer gewijzigd worden.

### 5.5 Competentiebeheer

- Admin kan competentieprofielen aanmaken per academiejaar.
- Competenties kunnen toegevoegd, gewijzigd en verwijderd worden.
- Gewichtenvalidatie: de som moet altijd 100% zijn.
- Competenties kunnen geactiveerd/gedeactiveerd worden.
- Bij aanmaak van een stage wordt het actieve profiel vastgelegd, zodat latere wijzigingen historische evaluaties niet beinvloeden.

### 5.6 Notificatiesysteem

- In-app notificaties via een bell-icoontje met badge voor ongelezen berichten.
- Auto-polling elke 30 seconden.
- Notificaties worden aangemaakt bij: voorstelindienen, beoordeling, overeenkomstvalidatie, logboekindiening, evaluatieafronding.
- Gebruikers kunnen notificaties als gelezen markeren (individueel of alles).

### 5.7 Audit Logging

- Alle belangrijke acties worden gelogd: statuswijzigingen, evaluatie-afrondingen, uploads, logins.
- Elke log bevat: tijdstip, actor (gebruiker + email + rol), actie, entiteit, en optioneel detail.
- Admin kan audit logs raadplegen en filteren per stage en per gebruiker.
- Audit logs zijn alleen-lezen en kunnen niet verwijderd worden.

### 5.8 Rapportages en Export

- Eindrapport per student: stage-informatie, logboekstatistieken, evaluatieoverzicht, gewogen eindscore.
- PDF-export van eindrapporten (gegenereerd met `fpdf2`).
- CSV-export van stage-overzichten voor administratie (UTF-8 met BOM voor Excel-compatibiliteit).
- Dashboard met statistieken: totaal aantal stages per status, logboekvoortgang, openstaande acties.

### 5.9 Gebruikersbeheer

- Volledige CRUD voor gebruikers (alleen admin).
- Zoeken en filteren op naam, email, rol.
- Paginatie voor grote gebruikerslijsten.

---

## 6. Technische Details

### 6.1 Dependencies

**Backend (Python):**

| Package | Versie | Gebruik |
|---|---|---|
| FastAPI | 0.109.0 | Web framework / REST API |
| Uvicorn | 0.27.0 | ASGI server |
| SQLAlchemy | >=2.0.40 | ORM voor database-interactie |
| Pydantic | >=2.10.0 | Data-validatie en schema's |
| python-jose | 3.3.0 | JWT token generatie en validatie |
| passlib + bcrypt | 1.7.4 | Wachtwoord hashing |
| python-multipart | 0.0.6 | File upload verwerking |
| fpdf2 | 2.7.9 | PDF-generatie voor eindrapporten |
| pytest + httpx | 7.4.4 / 0.26.0 | Testing |
| python-dotenv | 1.0.0 | Environment variabelen laden |
| PyYAML | 6.0.1 | Testdata seeding vanuit YAML |

**Frontend:**

| Package | Versie | Gebruik |
|---|---|---|
| Vite | ^5.0.0 | Dev server met hot reload en proxy |

De frontend gebruikt geen JavaScript frameworks. Alle logica is geschreven in vanilla JavaScript met ES modules.

### 6.2 API-structuur

Alle API endpoints zijn beschikbaar onder het `/api` prefix. De belangrijkste domeinen:

| Domein | Endpoints |
|---|---|
| Authenticatie | `POST /auth/login`, `POST /auth/register`, `GET /auth/me` |
| Stages | `GET /internships`, `POST /internships`, `GET /internships/{id}` |
| Voorstellen | `PATCH /internships/{id}/proposal`, `POST /internships/{id}/resubmit`, `GET /{id}/proposal/versions` |
| Overeenkomsten | `POST /internships/{id}/agreement`, `PATCH /internships/{id}/agreement` |
| Logboeken | `GET /internships/{id}/logbooks`, `POST /internships/{id}/logbooks`, `PATCH /logbooks/{id}` |
| Evaluaties | `GET /internships/{id}/evaluations`, `POST /internships/{id}/evaluations`, `POST /evaluations/{id}/finalize` |
| Competenties | `GET /competencies`, `POST /competencies/profiles`, `POST /competencies` |
| Feedback | `GET /internships/{id}/feedback`, `POST /internships/{id}/feedback` |
| Notificaties | `GET /notifications`, `PATCH /notifications/{id}/read`, `PATCH /notifications/read-all` |
| Rapportages | `GET /internships/{id}/final-report`, `GET /internships/reports/export/csv` |
| Audit | `GET /audit` |
| Gebruikers | `GET /users`, `POST /users`, `PATCH /users/{id}`, `DELETE /users/{id}` |
| Dashboard | `GET /me/dashboard`, `GET /internships/stats/dashboard` |

### 6.3 Environment Variabelen

| Variabele | Standaardwaarde | Beschrijving |
|---|---|---|
| `SECRET_KEY` | - | Vereist voor JWT tokens. Moet gewijzigd worden voor productie |
| `DATABASE_PATH` | `stage_monitoring.db` | Pad naar de SQLite database |
| `FRONTEND_ORIGINS` | `*` | Toegestane frontend URLs voor CORS (comma-separated) |

---

## 7. Deployment

### 7.1 Lokale ontwikkeling

Het project biedt startscripts voor alle platformen:

```bash
# macOS / Linux
./start.sh              # Start backend (poort 8001) + frontend (poort 8080)
./start.sh --backend    # Alleen backend
./start.sh --frontend   # Alleen frontend
./start.sh --reset      # Database resetten en opnieuw vullen

# Windows
start.bat               # Zelfde opties als start.sh
```

Het startscript detecteert automatisch of `uv` (snellere Python package manager) beschikbaar is en valt terug op `pip` als dat niet het geval is.

### 7.2 Docker

De applicatie draait in een enkele container die zowel backend als frontend serveert:

- Basis-image: `python:3.11-slim`
- Backend + frontend in een container
- Data wordt bewaard in een named volume (`stage-data`)
- Draait op poort 8080

```bash
docker compose up --build    # Bouwen en starten
docker compose up -d         # Op de achtergrond
```

### 7.3 Fly.io (productie-demo)

De applicatie is gedeployed op Fly.io met de volgende configuratie:

- Regio: London (`lhr`)
- VM: 256MB RAM, shared CPU
- Auto-stop bij inactiviteit (kostenbesparing)
- HTTPS afgedwongen
- Swagger UI uitgeschakeld in productie
- Rate limiting op authenticatie-endpoints

---

## 8. Testen

### 8.1 Backend tests

De backend bevat een uitgebreide pytest testsuite met de volgende testbestanden:

| Testbestand | Wat wordt getest |
|---|---|
| `test_auth.py` | Login, registratie, JWT-validatie |
| `test_internships.py` | CRUD operaties op stages, rolgebaseerde filtering |
| `test_lifecycle.py` | Statusovergangen, voorstelverwerking, herindiening |
| `test_agreements.py` | Overeenkomst upload en validatie |
| `test_competencies.py` | Competentiebeheer, gewichtenvalidatie |
| `test_users.py` | Gebruikersbeheer, CRUD, rolcontrole |
| `test_me_dashboard.py` | Dashboard-aggregatie per rol |
| `test_pagination_and_search.py` | Paginatie, zoeken, filteren |
| `test_csv_export.py` | CSV-export functionaliteit |
| `test_main.py` | Basis applicatie-opstart, health check |

Tests draaien met een in-memory SQLite database (`conftest.py` configureert een aparte test-database) zodat productiedata niet beinvloed wordt.

### 8.2 End-to-end test

Er is een uitgebreid end-to-end testscript (`e2e_full_flow.py`) dat het volledige stageproces doorloopt: van registratie tot eindrapport. Dit script valideert dat alle flows correct samenwerken.

### 8.3 Testdata

Testdata wordt geladen vanuit een YAML-bestand (`seed_data.yaml`) via `seed_loader.py`. Dit biedt realistische testdata voor alle rollen en fasen van het stageproces.

Standaard testaccounts:

| Rol | E-mail | Wachtwoord |
|---|---|---|
| Admin | admin@school.be | demo123 |
| Student | student1@school.be | student123 |
| Commissie | commissie1@school.be | commissie123 |
| Docent | docent1@school.be | docent123 |
| Mentor | mentor1@school.be | mentor123 |

---

## 9. Projectstructuur

```
Programming-Project-Group2-/
├── frontend/                         # Frontend applicatie
│   ├── index.html                   # Hoofdpagina met alle UI-templates
│   ├── styles.css                   # Styling
│   ├── js/
│   │   ├── app.js                   # Kernlogica: routing, formulieren
│   │   ├── api-client.js            # API-client modules
│   │   ├── ui-helpers.js            # UI utility functies
│   │   ├── notifications.js         # Notificatie bell + polling
│   │   └── views/                   # Rolgebonden views
│   │       ├── student.js
│   │       ├── teacher.js
│   │       ├── mentor.js
│   │       ├── committee.js
│   │       └── admin.js
│   ├── package.json
│   └── vite.config.js
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint + middleware
│   │   ├── database.py              # SQLAlchemy setup
│   │   ├── models.py                # Database-modellen (16 tabellen)
│   │   ├── auth.py                  # JWT + wachtwoord hashing
│   │   ├── dependencies.py          # Gedeelde FastAPI dependencies
│   │   ├── routers/                 # API endpoints (18 routers)
│   │   ├── schemas/                 # Pydantic schema's (13 bestanden)
│   │   └── services/               # Business logic (18 services)
│   ├── tests/                       # pytest testsuite (11 testbestanden)
│   ├── uploads/agreements/          # PDF uploads
│   ├── seed_data.yaml               # Testdata
│   ├── seed_loader.py               # YAML-based seeding
│   ├── e2e_full_flow.py             # End-to-end testscript
│   └── requirements.txt             # Python dependencies
├── docs/                             # Documentatie
│   ├── analyse-finaal.md            # Dit document
│   ├── architectuur.md              # Backend-architectuur (technisch)
│   ├── user-stories-overzicht.md    # Status per user story
│   ├── feature-todo.md              # Feature checklist
│   └── analyses/                    # Individuele analyses per teamlid
├── Dockerfile                        # Single-container build
├── docker-compose.yml                # Docker Compose configuratie
├── fly.toml                          # Fly.io deployment configuratie
├── start.sh / start.bat             # Cross-platform startscripts
└── start.py                          # Python-based startscript
```

---

## 10. Afwijkingen ten opzichte van de initiele analyse

Tijdens de ontwikkeling zijn er een aantal wijzigingen doorgevoerd ten opzichte van de oorspronkelijke analyse:

| Onderdeel | Initiele analyse | Uiteindelijke keuze | Reden |
|---|---|---|---|
| Frontend framework | React + Tailwind | Vanilla HTML/CSS/JS + Vite | Eenvoudiger opzet, minder leercurve, geen framework overhead |
| Backend framework | Node.js/Express of FastAPI | FastAPI (Python) | Team had meer ervaring met Python; FastAPI biedt automatische validatie |
| Database | PostgreSQL of MySQL | SQLite | Geen server-setup nodig, eenvoudigere deployment, voldoende voor dit project |
| Notificaties | E-mail service | In-app notificaties (polling) | E-mail was out of scope voor een eerstejaarsproject; in-app notificaties voldoen |
| Auth | JWT access/refresh tokens | JWT access token (24u) | Vereenvoudiging; refresh tokens niet nodig voor dit project |

---

## 11. Reflectie en Mogelijke Verbeteringen

### 11.1 Wat goed ging

- Alle 29 user stories zijn volledig geimplementeerd (zowel backend als frontend).
- De gelaagde architectuur maakte het project overzichtelijk en onderhoudbaar.
- De testsuite gaf vertrouwen bij refactoring en het toevoegen van nieuwe features.
- Docker en Fly.io maakten het eenvoudig om een werkende demo te tonen.
- Het competentieprofiel-systeem is flexibel opgezet met versiebeheer.

### 11.2 Mogelijke verbeteringen voor de toekomst

- **E-mailnotificaties**: naast in-app notificaties ook e-mails versturen bij belangrijke wijzigingen.
- **WebSocket-notificaties**: real-time notificaties in plaats van polling.
- **Database migraties**: Alembic migraties activeren voor schemawijzigingen zonder dataverlies.
- **Frontend framework**: bij verdere uitbreiding zou een framework zoals Vue of React de onderhoudbaarheid verbeteren.
- **PostgreSQL**: voor productiegebruik zou een robuustere database beter zijn.
- **Geautomatiseerde CI/CD**: GitHub Actions voor automatisch testen en deployen.
- **Accessibility**: verdere optimalisatie van de UI voor screenreaders en toetsenbordnavigatie.

---

## 12. Bronnen en Tools

### 12.1 Gebruikte tools

| Tool | Gebruik |
|---|---|
| GitHub | Versiebeheer en code reviews via pull requests |
| Trello | Taakopvolging (To Do, Bezig, Review, Klaar) |
| Microsoft Teams | Communicatie en afstemming |
| Docker | Containerisatie en deployment |
| Fly.io | Cloud hosting voor demo |
| Vite | Frontend dev server |
| pytest | Backend testing |

### 12.2 GitHub werkafspraken

- Geen directe pushes naar de `main` branch; deze bevat alleen werkende code.
- Ontwikkeling op feature branches (bijv. `feature/logboek`).
- Verplichte review door minstens een teamlid per pull request.
- Duidelijke en betekenisvolle commit messages.

### 12.3 Definition of Done

Een user story werd pas als "Done" beschouwd wanneer:

- Code gereviewd door minstens 1 teamlid
- Tests slagen
- Geen critical bugs open staan
- Validaties en foutmeldingen aanwezig zijn
- Documentatie is bijgewerkt
