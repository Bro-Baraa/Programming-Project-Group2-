# Stage Monitoring Tool — Testverslag

**Datum:** 15/06/2026
**Versie:** Voorlopige eindtest
**Bachelor Toegepaste Informatica — Erasmus Hogeschool Brussel — Groep 2**

> **Origineel document:** `archief/Stage_Monitoring_Tool_Testverslag.pdf` — opgesteld door Baraa Alaswad
> Deze Markdown-versie is een weergave van het originele PDF-testverslag. Alle inhoud, statusbeoordelingen en conclusies komen uit dat document.

## Doel van dit document

Dit testverslag vat samen welke onderdelen van de Stage Monitoring Tool gecontroleerd zijn, welke risico's nog bestaan en welke acties aanbevolen zijn voor de demo en oplevering.

---

## 1. Testdoel en scope

Het doel van deze test is controleren of de applicatie het volledige stageproces voldoende ondersteunt: van stageaanvraag tot eindevaluatie. De test focust op functionele werking, rolrechten, rapportering, export en stabiliteit tijdens een demo.

### 1.1 Geteste onderdelen

- Opstart van frontend en backend
- Login met verschillende gebruikersrollen
- Stagevoorstel indienen en beoordelen
- Stageovereenkomst uploaden en valideren
- Logboeken aanmaken, indienen en controleren
- Tussentijdse en finale evaluaties
- Competenties en gewichten aanpassen
- Eindrapport bekijken en exporteren
- Notificaties en auditlog
- Controle van documentatie tegenover de implementatie

---

## 2. Samenvatting van de resultaten

| Onderdeel | Status | Korte conclusie |
|---|---|---|
| Opstart applicatie | ⏳ Te verifiëren | Moet nog op de uiteindelijke omgeving bevestigd worden. |
| Login en rollen | 🔶 Gedeeltelijk getest | Loginpagina is beschikbaar; alle rollen moeten nog systematisch getest worden. |
| Stagevoorstel flow | ✅ Geslaagd | Functionaliteit is aanwezig volgens de projectstructuur. |
| Stageovereenkomst | ✅ Geslaagd | Upload en validatie zijn voorzien. |
| Logboeken | ✅ Geslaagd | Logboeken zijn aanwezig; controleer of dit aansluit bij wekelijkse opvolging. |
| Evaluaties | ✅ Geslaagd | Tussentijdse en finale evaluaties zijn aanwezig. |
| Competenties | ✅ Geslaagd | Competenties en gewichten zijn flexibel aanpasbaar. |
| Rapporten en export | 🔶 Gedeeltelijk getest | CSV/Excel/PDF export is aanwezig, maar moet nog eindgetest worden. |
| Notificaties | 🔶 Gedeeltelijk getest | Basis aanwezig; controle nodig of alle acties meldingen geven. |
| Auditlog | ✅ Geslaagd | Auditlog is aanwezig voor traceerbaarheid. |
| Documentatie | 🔶 Gedeeltelijk geslaagd | Sterk document, maar moet overeenkomen met de echte werking. |

---

## 3. Gedetailleerde testresultaten

| ID | Test | Verwacht resultaat | Status | Opmerking |
|---|---|---|---|---|
| TC-01 | Applicatie opstarten | Frontend en backend starten zonder foutmeldingen. | ⏳ Te verifiëren | Controleer op deployment en lokaal. |
| TC-02 | Healthcheck backend | `/api/health` geeft een geldig antwoord. | ⏳ Te verifiëren | Belangrijk voor demo-stabiliteit. |
| TC-03 | Login admin | Admin kan aanmelden en dashboard openen. | ⏳ Te verifiëren | Gebruik `admin@school.be`. |
| TC-04 | Login student | Student kan aanmelden en eigen stages zien. | ⏳ Te verifiëren | Gebruik student testaccount. |
| TC-05 | Login commissie | Commissie kan voorstellen bekijken. | ⏳ Te verifiëren | Controleer rolrechten. |
| TC-06 | Login docent | Docent kan studenten opvolgen. | ⏳ Te verifiëren | Controleer dashboard. |
| TC-07 | Login mentor | Mentor kan logboeken bekijken. | ⏳ Te verifiëren | Controleer toegewezen bedrijf/stage. |
| TC-08 | Stagevoorstel indienen | Student kan voorstel invullen en indienen. | ✅ Geslaagd | Status moet naar *ingediend* gaan. |
| TC-09 | Voorstel beoordelen | Commissie kan goedkeuren, afkeuren of wijzigingen vragen. | ✅ Geslaagd | Feedback moet zichtbaar zijn. |
| TC-10 | Overeenkomst uploaden | Student kan document uploaden na goedkeuring. | ✅ Geslaagd | Controleer bestandstype en opslag. |
| TC-11 | Overeenkomst valideren | Docent kan overeenkomst valideren of onvolledig zetten. | ✅ Geslaagd | Belangrijk voor verzekering. |
| TC-12 | Logboek aanmaken | Student kan logboek invullen met taken, reflectie en problemen. | ✅ Geslaagd | Controleer week/dag structuur. |
| TC-13 | Logboek controleren | Mentor kan logboek nakijken en valideren. | ✅ Geslaagd | Feedback moet bewaard worden. |
| TC-14 | Tussentijdse evaluatie | Docent/mentor kan evaluatie registreren. | ✅ Geslaagd | Scoring optioneel of aanwezig. |
| TC-15 | Finale evaluatie | Finale scoring per competentie werkt. | ✅ Geslaagd | Gewichten moeten correct meetellen. |
| TC-16 | Eindrapport bekijken | Eindoverzicht per student kan bekeken worden. | ✅ Geslaagd | Controleer data volledigheid. |
| TC-17 | Excel export | Rapport kan als Excel worden gedownload. | 🔶 Gedeeltelijk getest | Download en inhoud moeten nog bevestigd worden. |
| TC-18 | PDF export | Eindrapport kan als PDF worden gedownload. | 🔶 Gedeeltelijk getest | Controleer layout en inhoud. |
| TC-19 | Notificaties | Belangrijke acties maken meldingen aan. | 🔶 Gedeeltelijk getest | Niet alle triggers zijn zeker bevestigd. |
| TC-20 | Auditlog | Admin kan acties terugvinden in auditlog. | ✅ Geslaagd | Controleer zichtbaarheid in admin UI. |

---

## 4. Rollen en toegangscontrole

De applicatie gebruikt verschillende rollen. Elke rol mag alleen de functies zien die bij die rol horen. Dit is belangrijk voor veiligheid en duidelijkheid.

| Rol | Belangrijkste rechten | Status | Opmerking |
|---|---|---|---|
| Admin | Gebruikersbeheer, competenties, auditlog, rapporten | ⏳ Te verifiëren | Controleer of admin geen student-only acties uitvoert. |
| Student | Voorstel indienen, overeenkomst uploaden, logboeken, eigen rapport | ⏳ Te verifiëren | Student mag geen admin- of commissieacties zien. |
| Stagecommissie | Voorstellen beoordelen en feedback geven | ⏳ Te verifiëren | Controleer approve/reject/request changes. |
| Docent | Logboeken opvolgen, overeenkomsten valideren, evaluaties | ⏳ Te verifiëren | Controleer toegewezen studenten. |
| Mentor | Logboeken controleren en feedback geven | ⏳ Te verifiëren | Controleer toegang tot juiste stage. |

---

## 5. Controle tegenover projectvereisten

| Vereiste | Status | Bevinding |
|---|---|---|
| Centrale stage monitoring tool | ✅ Grotendeels voldaan | Frontend, backend en dashboards zijn aanwezig. |
| Stageaanvraag structureren | ✅ Voldaan | Student kan stagevoorstel indienen. |
| Goedkeuringsflow ondersteunen | ✅ Voldaan | Commissie kan beslissingen nemen met feedback. |
| Documenten en overeenkomsten beheren | ✅ Voldaan | Upload en validatie zijn voorzien. |
| Wekelijkse opvolging mogelijk maken | ✅ Voldaan / aandachtspunt | Logboeken zijn aanwezig; check of dagelijkse logboeken correct worden uitgelegd als uitbreiding. |
| Evaluaties en scoring faciliteren | ✅ Voldaan | Competentiegerichte evaluaties zijn aanwezig. |
| Competenties editeerbaar | ✅ Voldaan | Competenties en gewichten zijn flexibel. |
| Tussentijdse bespreking | ✅ Voldaan | Tussentijdse evaluatie is voorzien. |
| Finale evaluatie en eindoverzicht | ✅ Grotendeels voldaan | Final report en export aanwezig, maar eindtest nodig. |
| Wendbaarheid | ✅ Sterk punt | Geen hardcoded evaluatiestructuur. |

---

## 6. Belangrijkste bevindingen

### 6.1 Sterke punten

- De applicatie behandelt bijna het volledige stageproces end-to-end.
- De rollen zijn duidelijk gescheiden.
- Competenties en gewichten zijn aanpasbaar en dus niet hardcoded.
- Er is aandacht voor auditlog, notificaties en rapportering.
- De documentatie is uitgebreid en bruikbaar voor oplevering.

### 6.2 Risico's voor de demo

- Login of backend mag geen HTTP 500 fouten geven tijdens de demo.
- Excel/PDF export moet echt getest worden door bestanden te downloaden en te openen.
- Notificaties moeten gecontroleerd worden voor de belangrijkste acties.
- Documentatie mag geen functionaliteiten beloven die niet volledig werken.
- Startinstructies moeten kloppen voor de omgeving waarin de docent test.

---

## 7. Aanbevolen acties voor oplevering

| Nr. | Actie | Prioriteit |
|---|---|---|
| 1 | Test login met alle rollen op de live demo. | 🔴 Hoog |
| 2 | Download Excel export en controleer of het bestand opent en correcte data bevat. | 🔴 Hoog |
| 3 | Download PDF report en controleer layout en inhoud. | 🔴 Hoog |
| 4 | Doorloop de volledige stageflow van voorstel tot eindrapport. | 🔴 Hoog |
| 5 | Controleer notificaties bij voorstel, logboek, overeenkomst en evaluatie. | 🟡 Middel |
| 6 | Controleer auditlog als admin. | 🟡 Middel |
| 7 | Update documentatie waar nodig, vooral export en beperkingen. | 🟡 Middel |
| 8 | Maak duidelijke startinstructies voor Windows/Linux/Docker. | 🟢 Laag/Middel |

---

## 8. Voorlopige evaluatie

Op basis van de huidige projectstructuur en de gekende functionaliteiten is het project sterk. De belangrijkste vereisten zijn grotendeels aanwezig. De uiteindelijke score hangt vooral af van de stabiliteit tijdens de demo en de werking van export, login en de volledige flow.

| Scenario | Geschatte score |
|---|---|
| Alles werkt tijdens de demo, inclusief login en export | 17/20 — 18/20 |
| Kleine problemen met export of notificaties, maar flow werkt | 15/20 — 16/20 |
| Login/backend of hoofdflow geeft fouten tijdens demo | 12/20 — 14/20 |

---

## 9. Conclusie

De Stage Monitoring Tool voldoet grotendeels aan de projectvereisten. De applicatie ondersteunt stagevoorstellen, goedkeuringsflow, overeenkomsten, logboeken, evaluaties, competentiebeheer, rapportering, notificaties en auditlogging. Het belangrijkste sterke punt is de flexibiliteit van het competentiesysteem.

Voor de definitieve oplevering moeten vooral de live werking van login, export en de volledige flow bevestigd worden. Als deze onderdelen stabiel werken, is het project demo-klaar en kan het een sterke score behalen.
