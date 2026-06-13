**Stage Monitoring Tool**

Project Documentatie

Bachelor Toegepaste Informatica --- ErasmusHogeschoolBrussel

Academiejaar 2025--2026

Groep 2

**GitHub:** https://github.com/Bro-Baraa/Programming-Project-Group2-

**Trello:** [[Project_groep 2 WT \|
Trello]{.underline}](https://trello.com/b/aDORQ9Dz/projectgroep-2-wt)

Juan Benjumea-Moreno, Baraa Alaswad, Yorick Steehout, Samy Bekkaoui,
Léila Daif

# 1. Architectuur

De Stage Monitoring Tool is een webapplicatie die het volledige
stageproces ondersteunt. De applicatie heeft een duidelijke scheiding
tussen frontend, backend en database.

De frontend toont de schermen aan de gebruiker.\
De backend verwerkt de logica en bewaart gegevens via de database. De
communicatie gebeurt via een REST API.

## 1.1 Overzicht

  -----------------------------------------------------------------------
  **Laag**           **Technologie**
  ------------------ ----------------------------------------------------
  Frontend           HTML, CSS, Vanilla JavaScript (geen framework) +
                     Vite als bundler

  Backend            Python --- FastAPI (REST API framework)

  Database           SQLite (standaard)

  ORM/ Migraties     SQLAlchemy (ORM) + Alembic (database migration)

  Authenticatie      JWT-tokens (verlopen na 24 uur), bcrypt voor
                     wachtwoord-hashing

  PDF-generatie      fpdf2 (Python-bibliotheek voor rapporten)

  Containerisatie    Docker + Docker Compose (optioneel)

  CI/CD              GitHub Actions (automatische tests bij elke push)
  -----------------------------------------------------------------------

## 1.2 Mappenstructuur

Het project is als volgt georganiseerd:

> Programming-Project-Group2-/
>
> ├── frontend/ ← HTML/CSS/JS interface
>
> │ ├── index.html ← Hoofdpagina (Single Page App)
>
> │ ├── styles.css ← Stijlen
>
> │ └── js/ ← JavaScript-modules
>
> │ ├── app.js ← Hoofdlogica en routing
>
> │ ├── api-client.js ← Communicatie met de backend
>
> │ ├── views/ ← Per-rol weergaven
>
> │ │ ├── student.js
>
> │ │ ├── teacher.js
>
> │ │ ├── committee.js
>
> │ │ ├── mentor.js
>
> │ │ └── admin.js
>
> │ └── ui-helpers.js ← Herbruikbare UI-functies
>
> ├── backend/
>
> │ ├── app/
>
> │ │ ├── main.py ← FastAPI app + middleware
>
> │ │ ├── models.py ← Databasemodellen (SQLAlchemy)
>
> │ │ ├── auth.py ← JWT-authenticatie
>
> │ │ ├── routers/ ← API-endpoints per domein
>
> │ │ ├── schemas/ ← Pydantic-schemas (validatie)
>
> │ │ └── services/ ← Businesslogica
>
> │ ├── tests/ ← Automatische tests (pytest)
>
> │ ├── seed_data.yaml ← Testdata (YAML)
>
> │ └── requirements.txt ← Python-afhankelijkheden
>
> ├── docker-compose.yml
>
> ├── start.sh / start.bat ← Start-scripts
>
> └── .github/workflows/ ← CI/CD-pipelines

## 1.3 Communicatie tussen frontend en backend

De frontend is een Single Page Application (SPA). Dat betekent dat er
slechts één HTML-bestand is (index.html) en dat JavaScript zorgt voor
het wisselen van schermen. Alle data wordt opgehaald via
fetch()-aanroepen naar de backend.

De backend luistert op poort 8001 en de frontend op poort 8080.

Bij elke actie stuurt de frontend een HTTP-verzoek (GET, POST, PATCH,
DELETE) naar /api/\... en verwerkt het JSON-antwoord.

Beveiliging werkt met een JWT-token: na het inloggen ontvangt de
gebruiker een token dat bij elk verzoek in de Authorization-header wordt
meegestuurd. Elke route controleert of dit token geldig is en welke rol
de gebruiker heeft.

# 2. Gebruikersrollen

De applicatie kent vijf rollen. Elke rol heeft zijn eigen dashboard en
toegangsmogelijkheden. Een gebruiker heeft altijd precies één rol.

## 2.1 Student

> *Rol: student --- Dit is de hoofdgebruiker van het systeem.*

- Dient een stagevoorstel in.

- Volgt de status van het voorstel op.

- Past een voorstel aan wanneer de commissie feedback geeft.

- Uploadt de stageovereenkomst.

- Vult wekelijks een logboek in.

- Voert een zelfevaluatie uit op basis van competenties.

- Bekijkt feedback en het eigen eindrapport.

## 2.2 Stagecommissie

> *Rol: committee --- Beoordeelt en beslist over de ingediende
> stagevoorstellen.*

- Bekijkt ingediende stagevoorstellen.

- Keurt voorstellen goed of af.

- Vraagt aanpassingen wanneer een voorstel nog niet voldoende is.

- Voegt feedback toe bij de beslissing.

## 2.3 Docent

> *Rol: teacher --- Begeleidt studenten tijdens hun stage en voert
> evaluaties uit.*

- Volgt studenten op tijdens de stage.

- Bekijkt wekelijkse logboeken.

- Geeft feedback aan studenten.

- Valideert de stageovereenkomst.

- Voert tussentijdse en finale evaluaties in.

- Bekijkt het eindrapport per student.

## 2.4 Stagementor

> *Rol: mentor --- Medewerker van het stagebedrijf die de student
> dagelijks begeleidt.*

- Begeleidt de student binnen het bedrijf.

- Valideert wekelijkse logboeken.

- Geeft feedback vanuit het bedrijf.

- Kan een evaluatie invullen vanuit bedrijfsperspectief.

## 2.5 Administratie/ Admin

> *Rol: admin --- Beheert het hele systeem.*

- Beheert gebruikersaccounts (aanmaken, activeren, deactiveren)

- Beheert bedrijven in het systeem

- Beheert competentieprofielen en competenties

- Koppelt studenten aan docenten en mentors

- Bekijkt de audit-log (wie deed wat, en wanneer)

- Heeft toegang tot alle gegevens in het systeem

# 3. Functionaliteiten

## 3.1 Inloggen en authenticatie

Elke gebruiker logt in met e-mail en wachtwoord. Na het inloggen
ontvangt de browser een JWT-token. Op basis van de rol in het token
toont de frontend het juiste dashboard. Uitloggen verwijdert het token
uit de browser.

De applicatie bevat ook basisbeveiliging zoals wachtwoord-hashing en
rate limiting voor loginpogingen.

## 3.2 Stagevoorstel

Een student dient een voorstel in voor zijn/haar stage. Dit voorstel
doorloopt de volgende statussen:

  -----------------------------------------------------------------------
  **Status**            **Betekenis**
  --------------------- -------------------------------------------------
  Ingediend             Student heeft het voorstel ingediend en wacht op
                        beoordeling.

  Goedgekeurd           De stagecommissie heeft het voorstel goedgekeurd.

  Afgekeurd             Het voorstel is geweigerd.

  Aanpassingen vereist  De student moet het voorstel aanpassen op basis
                        van feedback.
  -----------------------------------------------------------------------

Van een voorstel kunnen versies worden bijgehouden. Zo blijft zichtbaar
welke aanpassingen eerder zijn gebeurd.

## 3.3 Stageovereenkomst

Na goedkeuring van het voorstel uploadt de student de stageovereenkomst.
Dit document is belangrijk voor de verzekering en moet door de juiste
personen ondertekend zijn. De docent kan het document controleren en
valideren.

Niet ingediend

Ingediend

Onvolledig

Gevalideerd

## 3.4 Wekelijkse logboeken

Tijdens de stage vult de student wekelijks een logboek in. In elk
logboek staan uitgevoerde taken, reflectie en eventuele problemen of
leerpunten. De mentor kan het logboek nakijken en valideren. De docent
kan de logboeken ook opvolgen.

## 3.5 Evaluaties

Evaluaties zijn gebaseerd op competenties die flexibel zijn ingesteld
per competentieprofiel. Er zijn twee soorten evaluaties:

- Tussentijdse evaluatie --- wordt halverwege de stage uitgevoerd

- Finale evaluatie --- wordt aan het einde van de stage uitgevoerd

Elke evaluatie kan worden ingevuld door drie partijen: de docent, de
mentor en de student (zelfevaluatie). Per competentie geeft de evaluator
een score van 1 tot 5 en optioneel feedback. Eens een evaluatie is
afgerond, kan ze niet meer worden aangepast.

## 3.6 Competenties

Competenties zijn volledig configureerbaar via de admin-interface. Ze
zijn gegroepeerd in competentieprofielen (bijv. één per richting en
academiejaar).

Elke competentie heeft een naam, beschrijving en gewicht (als
percentage). De gewichten worden gebruikt bij het berekenen van een
gewogen eindscore.

Voorbeeld van het standaardprofiel:

  -----------------------------------------------------------------------
  **Competentie**        **Beschrijving**                   **Gewicht**
  ---------------------- ---------------------------------- -------------
  Analyseren             Probleemanalyse, requirements,     30%
                         modellering                        

  Ontwerpen              Technisch ontwerp, architectuur,   25%
                         database                           

  Realiseren             Implementatie, clean code,         25%
                         versiebeheer                       

  Testen                 Kwaliteitsborging, unit tests,     20%
                         CI/CD                              
  -----------------------------------------------------------------------

## 3.7 Berichten en feedback

Docenten, mentors en studenten kunnen berichten sturen via het
ingebouwde berichtensysteem. Berichten zijn altijd gekoppeld aan een
specifieke stage. Er is geen algemene inbox --- alles is in context.

## 3.8 Notificaties

Het systeem stuurt automatisch meldingen bij belangrijke gebeurtenissen,
zoals: een nieuw voorstel ingediend, een voorstel goedgekeurd of
afgekeurd, een logboek ingediend, een overeenkomst gevalideerd, een
evaluatie beschikbaar gesteld.

Notificaties zijn zichtbaar in de navigatiebalk en kunnen als
\'gelezen\' worden gemarkeerd.

## 3.9 Dashboard

Elke rol heeft een eigen dashboard met een overzicht op maat.

Studenten zien hun actieve stages en openstaande acties.

Docenten zien alle studenten die aan hen zijn toegewezen.

De admin ziet systeemstatistieken. Alles is gefilterd op wat relevant is
voor die rol.

## 3.10 Eindrapport

Per student kan een eindrapport worden gegenereerd. Dit rapport bevat
een samenvatting van de stage, de logboeken, de evaluatiescores per
competentie met gewogen berekening, en de feedback van alle betrokken
partijen. Het rapport kan worden bekeken in de browser of als PDF worden
gedownload via de API.

## 3.11 Auditlog (Admin)

Alle acties in het systeem worden bijgehouden in een auditlog: wie deed
wat, op welk tijdstip, en vanuit welk IP-adres. Dit is enkel
toegankelijk voor de admin en dient als beveiliging en traceerbaarheid.

# 4. Database

De applicatie gebruikt SQLite als standaard database. De structuur wordt
beheerd via SQLAlchemy (Python ORM) en databasemigraties verlopen via
Alembic.

Overstappen naar PostgreSQL of MySQL is mogelijk door de
verbindingsstring in app/database.py aan te passen.

## 4.1 Tabeloverzicht

+-------------------------+----------------------------------------------------+
| **Tabel**               | **Beschrijving**                                   |
+=========================+====================================================+
| **users**               | Alle gebruikers: student, teacher, committee,      |
|                         | mentor, admin.                                     |
|                         |                                                    |
|                         | Bevat email, gehashed wachtwoord, naam, rol en     |
|                         | actief-status.                                     |
+-------------------------+----------------------------------------------------+
| **companies**           | Stagebedrijven: naam, adres, sector,               |
|                         | contactpersoon en een optionele koppeling aan een  |
|                         | mentor-gebruiker.                                  |
+-------------------------+----------------------------------------------------+
| **internships**         | Centrale stagegegevens met student, docent,        |
|                         | mentor, bedrijf, periode en status.                |
+-------------------------+----------------------------------------------------+
| **proposals**           | Het stagevoorstel van een student: beschrijving,   |
|                         | huidige status, feedback van de commissie en het   |
|                         | versienummer.                                      |
+-------------------------+----------------------------------------------------+
| **proposal_versions**   | Historiek van alle vorige versies van een          |
|                         | stagevoorstel (met datum en status per versie).    |
+-------------------------+----------------------------------------------------+
| **agreements**          | De stageovereenkomst: bestandspad, of de           |
|                         | verzekering is geverifieerd, en de huidige status  |
|                         | (Ingediend, Gevalideerd...).                       |
+-------------------------+----------------------------------------------------+
| **logbooks**            | Wekelijkse logboeken: weeknummer, taken,           |
|                         | reflectie, problemen, status (draft/ingediend),    |
|                         | feedback van de mentor en validatiestatus.         |
+-------------------------+----------------------------------------------------+
| **competency_profiles** | Een groep competenties, gekoppeld aan een          |
|                         | opleiding en academiejaar. Kan actief of inactief  |
|                         | zijn.                                              |
+-------------------------+----------------------------------------------------+
| **competencies**        | Een individuele competentie met naam,              |
|                         | beschrijving, gewicht en of ze actief is.          |
+-------------------------+----------------------------------------------------+
| **evaluations**         | Een evaluatie per stage per evaluator (type:       |
|                         | tussentijds of final). Bevat algemeen commentaar   |
|                         | en of ze is afgerond.                              |
+-------------------------+----------------------------------------------------+
| **evaluation_rules**    | De score (1-5) per competentie binnen een          |
|                         | evaluatie, plus een snapshot van het gewicht op    |
|                         | het moment van evaluatie.                          |
+-------------------------+----------------------------------------------------+
| **feedback**            | Berichten tussen gebruikers, altijd gekoppeld aan  |
|                         | een stage.                                         |
+-------------------------+----------------------------------------------------+
| **notifications**       | Systeemmeldingen per gebruiker                     |
|                         | (gelezen/ongelezen), met een optionele koppeling   |
|                         | naar een stage en een weergavelink.                |
+-------------------------+----------------------------------------------------+
| documents               | Extra documenten bij een stage (bestandspad en     |
|                         | documenttype).                                     |
+-------------------------+----------------------------------------------------+
| audit_logs              | Auditlog: elke actie wordt geregistreerd met       |
|                         | gebruiker, tijdstip, actie, entiteit en IP-adres.  |
+-------------------------+----------------------------------------------------+

## 4.2 Statuswaarden

Hieronder een overzicht van de mogelijke statuswaarden per entiteit:

**Stage (internship.status)**

- Ingediend: voorstel ingediend, nog niet goedgekeurd

- Goedgekeurd: voorstel goedgekeurd, wacht op overeenkomst

- Overeenkomst Ingediend: overeenkomst geüpload, wacht op validatie

- Lopend: overeenkomst gevalideerd, stage is actief

- Afgekeurd: voorstel definitief afgekeurd

- Afgerond: stage volledig afgerond

**Stagevoorstel (proposal.status)**

- Ingediend

- Goedgekeurd

- Afgekeurd

- Aanpassingen vereist

**Stageovereenkomst (agreement.status)**

- Niet Ingediend

- Ingediend

- Onvolledig

- Gevalideerd

**Logboek (logbook.status)**

- Draft: in opbouw, nog niet ingediend

- Ingediend: ingediend bij mentor

- Gevalideerd: goedgekeurd door mentor

# 5. Installatie Handleiding

Hieronder vind je stap voor stap hoe je de applicatie lokaal opstart. Er
zijn twee manieren: via het start-script of via Docker.

## 5.1 Vereisten

- Python 3.11 of hoger

- Node.js 18 of hoger (voor de frontend)

- uv (Python package manager) --- of pip als alternatief

- Git

- npm

- Optioneel: Docker en Docker Compose (voor de containerversie)

## 5.2 Snelste manier (aanbevolen)

1\. Kloon de repository:

> git clone https://github.com/Bro-Baraa/Programming-Project-Group2-
>
> cd Programming-Project-Group2-

2\. Installeer de frontend-afhankelijkheden:

> cd frontend && npm install && cd ..

3\. Maak het .env-bestand aan voor de backend:

> cd backend
>
> cp .env.example .env

4\. Start alles in één keer:

> ./start.sh

Of op Windows:

> start.bat

De backend is nu bereikbaar op http://localhost:8001 en de frontend op
http://localhost:8080.

## 5.3 Inhoud van het .env-bestand

Het bestand backend/.env bevat de volgende instellingen:

> SECRET_KEY=een-willekeurige-geheime-string-hier
>
> DATABASE_PATH=stage_monitoring.db
>
> FRONTEND_ORIGINS=http://localhost:8080
>
> API_PORT=8001

Pas SECRET_KEY aan naar een eigen willekeurige string voor
productieomgevingen.

## 5.4 Database opvullen met testdata

Bij de eerste opstart is de database leeg. Je kan testdata laden via:

> ./start.sh \--reset

Dit reset de database en laadt alle testgebruikers en -stages vanuit het
bestand backend/seed_data.yaml. Je kan dat bestand ook zelf aanpassen om
andere testdata te gebruiken.

## 5.5 Start-opties

  -----------------------------------------------------------------------
  **Commando**           **Wat doet het?**
  ---------------------- ------------------------------------------------
  ./start.sh             Start backend én frontend tegelijk

  ./start.sh \--backend  Start alleen de backend (poort 8001)

  ./start.sh \--frontend Start alleen de frontend (poort 8080)

  ./start.sh \--reset    Reset database en laad testdata opnieuw

  ./start.sh \--help     Toon alle beschikbare opties
  -----------------------------------------------------------------------

## 5.6 Starten via Docker (alternatief)

Als Docker is geïnstalleerd, kan je de hele applicatie in containers
draaien:

> docker-compose up \--build

Dit bouwt de containers en start zowel backend als frontend. Handig als
je geen Python of Node.js lokaal wil installeren.

## 5.7 Automatische tests uitvoeren

De backend heeft een uitgebreide testsuite gebouwd met pytest:

> cd backend
>
> pytest

Of via het meegeleverde script:

> ./run_tests.sh

De tests controleren authenticatie, stagevoorstellen, logboeken,
evaluaties, notificaties, bedrijven, overeenkomsten en meer. De
CI/CD-pipeline op GitHub voert deze tests ook automatisch uit bij elke
push naar de repository.

# 6. Testaccounts

Na het laden van de testdata (./start.sh \--reset) zijn de volgende
accounts beschikbaar. Elk account heeft een eigen rol en bijhorende
rechten.

## 6.1 Hoofdaccounts per rol

  -------------------------------------------------------------------------
  **Rol**          **E-mail**                 **Wachtwoord**    **Naam**
  ---------------- -------------------------- ----------------- -----------
  Admin            admin@school.be            demo123           System
                                                                Beheerder

  Student          student1@school.be         student123        Jan Peeters

  Stagecommissie   commissie1@school.be       commissie123      Peter Smit

  Docent           docent1@school.be          docent123         Ann
                                                                Claessens

  Mentor           mentor1@school.be          mentor123         Mentor Eén
  -------------------------------------------------------------------------

## 6.2 Alle beschikbare studentaccounts

Er zijn meerdere studentaccounts met verschillende scenario\'s om de
applicatie te demonstreren:

  ------------------------------------------------------------------------
  **E-mail**            **Wachtwoord**   **Scenario**
  --------------------- ---------------- ---------------------------------
  student1@school.be    student123       Sterke student: één afgeronde
                                         stage en één lopende stage

  student2@school.be    student123       Afgeronde stage (cybersecurity) +
                                         nieuwe stage in opstartfase

  student3@school.be    demo123          Afgekeurd voorstel gevolgd door
                                         een goedgekeurd nieuw voorstel

  student4@school.be    demo123          Lopende stage bij game-studio,
                                         goede evaluaties

  student5@school.be    demo123          Afgeronde stage met moeizaam
                                         verloop en slechte evaluaties

  student7@school.be    demo123          Lopende AI-stage, recent gestart

  student8@school.be    demo123          Lopende stage met onvolledige
                                         overeenkomst
  ------------------------------------------------------------------------

## 6.3 Mentor accounts per bedrijf

  ---------------------------------------------------------------------------
  **E-mail**                  **Wachtwoord**     **Bedrijf**
  --------------------------- ------------------ ----------------------------
  b.janssens@techcorp.be      mentor123          TechCorp BV

  s.devries@dataflow.be       mentor123          DataFlow Solutions

  p.maes@securenet.be         mentor123          SecureNet

  n.kowalski@innovatelab.be   mentor123          InnovateLab

  r.decock@gamestudiox.be     mentor123          GameStudio X
  ---------------------------------------------------------------------------

# 7. Bekende beperkingen

Hieronder een eerlijk overzicht van wat nog niet (volledig) werkt of
ontbreekt in de huidige versie:

## 7.1 Export

- PDF-export van het eindrapport is gedeeltelijk aanwezig via de API
  (/api/internships/{id}/report/pdf).

- Excel-export (bijv. een overzicht van alle stages of evaluaties) is
  technisch aanwezig via openpyxl.

## 7.2 Bestandsopslag

- Geüploade documenten worden lokaal opgeslagen in een uploads-map.

- Er is nog geen integratie met cloudopslag zoals S3 of Google Drive.

- Bij Docker moet de uploads-map persistent gemount worden om bestanden
  te bewaren.

## 7.3 Beveiliging

- De rate-limiting (max. 10 verzoeken/minuut per IP) is in-memory en
  werkt niet correct bij meerdere serverinstanties.

> Voor productie is een externe oplossing zoals Redis aangeraden.

- Er is geen e-mailverificatie bij registratie. Accounts worden
  rechtstreeks aangemaakt door de admin.

- Wachtwoord-reset via e-mail is niet geïmplementeerd.

> Admins moeten wachtwoorden handmatig resetten.

## 7.4 Schaalbaarheidsbeperkingen

- De applicatie gebruikt SQLite als standaard database. SQLite is
  geschikt voor ontwikkeling en kleine groepen, maar voor productie met
  meerdere gelijktijdige gebruikers is PostgreSQL sterk aanbevolen.

- Er is geen paginering op alle overzichten --- bij zeer veel gegevens
  (honderden stages) kan de interface trager worden.

# 8. Belangrijkste API-endpoints

Alle endpoints beginnen met /api/. Authenticatie via een Bearer-token in
de Authorization-header is verplicht, tenzij anders vermeld.

  -----------------------------------------------------------------------------------
  **Methode**   **Endpoint**                    **Beschrijving**
  ------------- ------------------------------- -------------------------------------
  POST          /auth/login                     Inloggen --- geen token vereist

  GET           /auth/me                        Huidige ingelogde gebruiker ophalen

  GET           /me/dashboard                   Dashboard-data voor de ingelogde
                                                gebruiker

  GET           /internships                    Lijst van stages (gefilterd op rol)

  POST          /internships                    Nieuwe stage aanmaken (admin/teacher)

  POST          /internships/{id}/proposal      Stagevoorstel indienen (student)

  PATCH         /internships/{id}/proposal      Voorstel beoordelen (commissie)

  POST          /internships/{id}/resubmit      Voorstel opnieuw indienen na feedback
                                                (student)

  POST          /internships/{id}/agreement     Overeenkomst uploaden (student)

  PATCH         /internships/{id}/agreement     Overeenkomst valideren (teacher)

  GET           /internships/{id}/logbooks      Logboeken ophalen

  POST          /internships/{id}/logbooks      Nieuw logboek aanmaken (student)

  GET           /internships/{id}/evaluations   Evaluaties ophalen

  POST          /internships/{id}/evaluations   Evaluatie aanmaken

  GET           /internships/{id}/report        Eindrapport ophalen (JSON)

  GET           /competencies                   Competentieprofielen ophalen

  GET           /users                          Gebruikersbeheer (admin)

  GET           /notifications                  Notificaties voor de ingelogde
                                                gebruiker

  GET           /audit                          Auditlog (enkel admin)

  GET           /api/health                     Healthcheck --- geen token vereist
  -----------------------------------------------------------------------------------

#    10. Conclusie

De Stage Monitoring Tool ondersteunt het stageproces van aanvraag tot
opvolging en evaluatie. De belangrijkste onderdelen zijn aanwezig:
rollenbeheer, stagevoorstellen, goedkeuringsflow, stageovereenkomst,
logboeken, competentiegerichte evaluaties, notificaties en rapportage.

De applicatie is modulair opgebouwd en kan later uitgebreid worden.
Vooral het flexibele competentiesysteem is belangrijk, omdat de
opleiding evaluatiecriteria kan aanpassen zonder de evaluatiestructuur
hard te coderen.

De belangrijkste aandachtspunten voor verdere ontwikkeling zijn betere
export naar PDF/Excel, cloudopslag voor documenten, e-mailnotificaties
en productieklare beveiliging.
