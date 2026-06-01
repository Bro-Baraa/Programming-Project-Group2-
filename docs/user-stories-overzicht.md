# User Stories Overzicht – Stagetool Groep 2

Bron: analyse-finaal.md × Codebase audit
Datum: 2026-05-27

---

## Statuscodes

| Code | Betekenis |
|------|-----------|
| OK | Zowel backend als frontend volledig geïmplementeerd |
| BE-OK | Backend volledig; frontend mist (of gedeeltelijk) |
| PART | Backend + frontend aanwezig, maar met beperkende hiaten |
| BUG | Fundamenteel probleem; functionaliteit ondermijnd |
| NOK | Niet geïmplementeerd |

## Fase 1: Aanvraag

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-01 | Student dient stagevoorstel in met bedrijfs- en opdrachtgegevens | PART | `POST /internships` maakt Internship + Company + Proposal in een keer. `teacher_id`/`mentor_id` ondersteund met validatie. | Stagevoorstel-formulier mist velden voor docent/mentor kiezen. Student kan niet zelf begeleiders aanduiden bij indiening. | Geen UI voor supervisor selectie. Kan later door staff worden toegewezen via `PATCH /internships`. |
| US-02 | Student bekijkt status stagevoorstel | OK | `GET /internships/{id}`, `GET /internships/{id}/proposal`, `GET /me/dashboard` retourneren status. | Dashboard toont status-pill; proposal status zichtbaar in detail. | — |
| US-10 | Commissie ziet lijst voorstellen | OK | `GET /internships` retourneert alle stages met `proposal_status`, zoeken, filteren, paginatie. | Tabel met sorteerbare rijen; overzichtelijke weergave student + bedrijf + status. | — |
| US-24 | Mentor ziet stagecontext | OK | `GET /internships/{id}` toont context; rol-gefilterde toegang. | Stage-selector dropdown; mentor ziet alleen stages waar `mentor_id` op hem staat. | — |

## Fase 2: Beoordeling

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-03 | Student ontvangt feedback bij afkeuring of aanpassingen | PART | `Proposal.feedback` veld beschikbaar via `GET /proposal`. | Feedback wordt getoond in student dashboard. | Geen push-notificatie; student moet actief pollen of dashboard bezoeken. |
| US-11 | Commissie keurt goed, af, of vraagt aanpassingen | PART | `PATCH /internships/{id}/proposal` met `review_proposal()`. | Goedkeuren / afkeuren / aanpassingen knoppen beschikbaar. | Status "In Beoordeling" (tussenstap uit analyse) ontbreekt in `_TRANSITIONS`. Commissie springt direct van "Ingediend" naar beslissing. |
| US-12 | Commissie geeft feedback mee bij beslissing | OK | `feedback` is verplicht bij "Aanpassingen Vereist". | Feedback textarea bij review panel. | — |
| US-20 | Docent ontvangt notificatie bij nieuwe logboeken | NOK | Geen notificatie-infrastructuur. | Geen notificatie UI (bell, toast, badge). | Zie feature-todo #2: Notificatiesysteem. |

## Fase 3: Overeenkomst

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-04 | Student uploadt stageovereenkomst | OK | `POST /internships/{id}/agreement` accepteert PDF; content-type validatie op `application/pdf`; status wijzigt naar "Overeenkomst Ingediend". | Upload formulier met file picker + PDF accept attribuut. | — |
| US-13 | Commissie controleert of overeenkomst is opgeladen | PART | `GET /agreement` toont status. `PATCH /agreement` markeert als "Gevalideerd" of "Onvolledig". | Agreement status zichtbaar in commissie overzicht. | Rol "administratie" bestaat niet in het systeem; committee/admin voert deze actie uit. |
| US-26 | Administratie ziet welke studenten overeenkomst hebben ingediend | PART | `GET /internships/reports/agreements` geeft agreement-status. | Commissie overzicht toont "Overeenkomst" kolom met ontvangen/nog-niet. | Zelfde rol-probleem als US-13; geen dedicated "administratie" rol. |

## Fase 4: Opvolging

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-05 | Student vult wekelijks logboek in met taken en reflecties | PART | `POST /logbooks` en `PATCH /logbooks/{id}` werken. Velden: tasks, reflection, issues. | Logboek formulier met week, taken, reflectie, problemen. | Geen expliciete "definitief indienen" actie; generieke PATCH zet `status` op "submitted". Max 1 per week alleen afgedwongen bij create, niet bij update. |
| US-06 | Student beschrijft per competentie wat hij geleerd heeft | OK | `PATCH /evaluations/{id}/rules/{rule_id}` gebruikt `get_current_active_user`; service laag beperkt student tot `student_description`. | Student beschrijving veld zichtbaar in evaluatie formulier. | — |
| US-07 | Student leest feedback van docent/mentor | PART | `GET /internships/{id}/feedback` retourneert feedback. | Feedback sectie op student dashboard toont berichten. | Feedback is generiek (from_user, to_user, message); niet gekoppeld aan specifieke logboek-week. |
| US-08 | Student ziet historiek van logboeken | PART | `GET /internships/{id}/logbooks` en `GET .../logbooks/weeks` bestaan, met "missing" markering. | Logboek-tabel in dashboard toont alleen bestaande logboeken; frontend gebruikt de week-overview niet. | Ontbrekende weken worden niet visueel weergegeven in de student UI. |
| US-14 | Commissie ziet overzicht alle stages en statussen | OK | `GET /internships` en `GET /stats/dashboard`. | Overzicht tabel + statistieken paneel met totalen. | — |
| US-15 | Docent ziet wekelijkse logboeken | OK | `GET /internships/{id}/logbooks` beschikbaar voor docent. | Docent logboek-tabel met week, taken, reflectie, status, mentor validatie. | — |
| US-16 | Docent geeft feedback per competentie | PART | `evaluator_feedback` in `EvaluationRule` werkt via PATCH. | Evaluatie formulier heeft feedback veld per competentie. | Gekoppeld aan evaluaties (Evaluatie-fase), niet aan logboeken (Opvolging-fase). Geen mogelijkheid om feedback te geven op specifieke logboek-week. |
| US-17 | Docent registreert tussentijdse evaluatie | OK | `POST /evaluations` met `eval_type: "tussentijds"`. | Evaluatie formulier met type selector (tussentijds/final). | — |
| US-21 | Mentor ziet wekelijks logboeken | OK | `GET /internships/{id}/logbooks` beschikbaar voor mentor. | Mentor logboek-tabel met validate-knoppen. | — |
| US-22 | Mentor tekent logboeken af | PART | `PATCH /logbooks/{id}` met `mentor_validated=true`. | "Valideren" knop per logboek rij in mentor view. | Geen dedicated sign-off endpoint. Mentor moet generieke update gebruiken met specifiek veld. |

## Fase 5: Evaluatie

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-09 | Student raadpleegt eindevaluatierapport | PART | `GET /evaluations/{id}` met score; `GET /internships/{id}/final-report` geeft eindoverzicht. | Student evaluatie view toont evaluatie tabel, maar **eindoverzicht is statische tekst** ("nog niet ingediend"). Frontend haalt `/final-report` endpoint niet op. | Eindrapport data wordt niet daadwerkelijk opgehaald en getoond. |
| US-18 | Docent vult finale evaluatie in met score per competentie | PART | `POST /evaluations` (type final) + `PATCH /evaluations/{id}/rules/{rule_id}` met score. Automatische gewogen eindscore. `POST /evaluations/{id}/finalize` lockt evaluatie. | Evaluatie formulier toont score selectors per competentie + afronden knop. | Geen bulk-update endpoint; docent moet per competentie een aparte PATCH call doen (frontend doet dit wel automatisch). |
| US-19 | Docent genereert eindoverzicht per student | BE-OK | `GET /internships/{id}/final-report` retourneert `FinalReportItem` met gewogen score. | **Geen frontend view** voor eindoverzicht bij docent. Alleen backend endpoint beschikbaar. | Docent mist scherm om eindrapport te bekijken/afdrukken. |
| US-23 | Mentor geeft feedback per competentie | OK | Zelfde endpoint als US-16; mentor toegang via `require_any_staff`. | Mentor heeft een eigen evaluatiescherm en kan feedback per competentie invullen. | — |

## Configuratie & Beheer

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-25 | Administratie beheert competenties en gewichten | PART | Volledige CRUD: CompetencyProfile + Competency endpoints. Gewichten-validatie (som = 100%). Actief/inactief toggelen. | Admin competentiebeheer: toevoegen, verwijderen, gewichten zien, score simulator. | **Geen versiebeheer**: acceptatiecriterium eist dat wijzigingen enkel voor nieuwe stageperiodes gelden en historische evaluaties ongewijzigd blijven. Dit is niet geïmplementeerd. |
| US-27 | Administratie beheert gebruikers | BE-OK | Volledige CRUD: `GET /users`, `GET /users/{id}`, `POST /users`, `PATCH /users/{id}`, `DELETE /users/{id}`. Alleen admin toegang. | Geen admin UI voor gebruikersbeheer. | Backend compleet. Frontend moet admin scherm toevoegen voor aanmaken, wijzigen en verwijderen. |
| US-28 | Administratie exporteert rapportages | NOK | Rapportage endpoints retourneren JSON. | Geen export UI (download CSV/XLSX/PDF knoppen). | Geen CSV/XLSX/PDF export. Zie feature-todo #5. |

## Overkoepelend

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-29 | Gebruiker krijgt melding bij relevante wijziging | NOK | Geen notificatie-infrastructuur. | Geen notificatie UI (bell, badge, toast bij wijziging). | Geen e-mail, push, in-app, websocket of event queue. Zie feature-todo #2. |

---

## Samenvatting per Status

| Status | Aantal |
|--------|--------|
| OK | 12 |
| BE-OK | 2 |
| PART | 11 |
| BUG | 0 |
| NOK | 3 |

## Top prioriteiten (gesorteerd)

1. **US-19 (BE-OK)** — Eindoverzicht frontend view toevoegen voor docent
2. **US-09 (PART)** — Eindrapport daadwerkelijk ophalen en tonen in student view
3. **US-29 + US-20 (NOK)** — Notificatiesysteem implementeren
4. **US-25 (PART)** — Competentieprofiel koppelen aan stage zodat historische evaluaties stabiel blijven
5. **US-28 (NOK)** — Export rapportages (CSV/XLSX/PDF)
6. **US-11 (PART)** — Status "In Beoordeling" toevoegen aan proposal lifecycle
