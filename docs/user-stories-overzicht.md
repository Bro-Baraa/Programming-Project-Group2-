# User Stories Overzicht - Stagetool Groep 2

Bron: `analyse-finaal.md` x codebase audit
Datum: 2026-06-02

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
| US-01 | Student dient stagevoorstel in met bedrijfs- en opdrachtgegevens | PART | `POST /internships` maakt Internship + Company + Proposal in een keer. `teacher_id`/`mentor_id` worden ondersteund met validatie. | Stagevoorstel-formulier mist velden om docent/mentor te kiezen. | Backend kan de relaties opslaan, maar de student kan ze niet zelf aanduiden in de UI. |
| US-02 | Student bekijkt status stagevoorstel | OK | `GET /internships/{id}`, `GET /internships/{id}/proposal`, `GET /me/dashboard` retourneren status. | Dashboard toont status-pill; proposal status zichtbaar in detail. | - |
| US-10 | Commissie ziet lijst voorstellen | OK | `GET /internships` retourneert stages met `proposal_status`, zoeken, filteren en paginatie. | Tabel met sorteerbare rijen; overzichtelijke weergave student + bedrijf + status. | - |
| US-24 | Mentor ziet stagecontext | OK | `GET /internships/{id}` toont context; rol-gefilterde toegang. | Stage-selector dropdown; mentor ziet alleen stages waar `mentor_id` op hem staat. | - |

## Fase 2: Beoordeling

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-03 | Student ontvangt feedback bij afkeuring of aanpassingen | PART | `Proposal.feedback` is beschikbaar via `GET /proposal`. | Feedback wordt getoond in student dashboard. | Geen notificatieflow; student moet het dashboard openen. |
| US-11 | Commissie keurt goed, af, of vraagt aanpassingen | OK | `PATCH /internships/{id}/proposal` met `review_proposal()`. | Reviewscherm ondersteunt eerst "In Beoordeling" zetten, daarna een beslissing. | Twee-staps reviewflow werkt nu in UI en backend. |
| US-12 | Commissie geeft feedback mee bij beslissing | OK | `feedback` is verplicht bij "Aanpassingen Vereist". | Feedback textarea bij review panel. | - |
| US-20 | Docent ontvangt notificatie bij nieuwe logboeken | NOK | Geen notificatie-infrastructuur. | Geen notificatie UI (bell, toast, badge). | Zie `feature-todo.md` item 2. |

## Fase 3: Overeenkomst

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-04 | Student uploadt stageovereenkomst | OK | `POST /internships/{id}/agreement` accepteert PDF; content-type validatie op `application/pdf`; status wijzigt naar "Overeenkomst Ingediend". | Upload formulier met file picker + PDF accept attribuut. | — |
| US-13 | Commissie controleert of overeenkomst is opgeladen | OK | `GET /agreement` toont status. `PATCH /agreement` markeert als "Gevalideerd" of "Onvolledig". | Commissie heeft "Overeenkomsten" tab met lijst, PDF download, verzekeringscheckbox, en validatieknoppen. | — |
| US-26 | Administratie ziet welke studenten overeenkomst hebben ingediend | PART | `GET /internships/reports/agreements` geeft agreement-status. | Commissie overzicht toont "Overeenkomst" kolom met ontvangen/nog-niet. | Zelfde rol-probleem als US-13; geen dedicated "administratie" rol. |

## Fase 4: Opvolging

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-05 | Student vult wekelijks logboek in met taken en reflecties | OK | `POST /logbooks` en `PATCH /logbooks/{id}` werken. `POST /logbooks/{id}/submit` voor definitief indienen. Velden: tasks, reflection, issues. | Logboekformulier met "Opslaan als Concept" en "Definitief Indienen". | - |
| US-06 | Student beschrijft per competentie wat hij geleerd heeft | PART | `PATCH /evaluations/{id}/rules/{rule_id}` laat `student_description` opslaan. | Er is geen student-specifieke flow; het veld zit alleen in de docent/mentor evaluatie-UI. | Backend kan het, maar de student UI niet. |
| US-07 | Student leest feedback van docent/mentor | PART | `GET /internships/{id}/feedback` retourneert feedback. | Feedback sectie op student dashboard toont berichten. | Feedback is generiek (`from_user`, `to_user`, `message`); niet gekoppeld aan een logboek-week. |
| US-08 | Student ziet historiek van logboeken | PART | `GET /internships/{id}/logbooks` en `GET .../logbooks/weeks` bestaan, met "missing" markering. | Logboek-tabel toont alleen bestaande logboeken; frontend gebruikt de week-overview niet. | Ontbrekende weken worden niet visueel weergegeven in de student UI. |
| US-14 | Commissie ziet overzicht alle stages en statussen | OK | `GET /internships` en `GET /stats/dashboard`. | Overzichtstabel + statistiekenpaneel met totalen. | - |
| US-15 | Docent ziet wekelijkse logboeken | OK | `GET /internships/{id}/logbooks` beschikbaar voor docent. | Docent logboek-tabel met week, taken, reflectie, status, mentor validatie. | - |
| US-16 | Docent geeft feedback per competentie | PART | `evaluator_feedback` in `EvaluationRule` werkt via PATCH. | Evaluatieformulier heeft feedback veld per competentie. | Gekoppeld aan evaluaties, niet aan logboeken. Geen feedback op specifieke logboek-week. |
| US-17 | Docent registreert tussentijdse evaluatie | OK | `POST /evaluations` met `eval_type: "tussentijds"`. | Evaluatieformulier met type selector (tussentijds/final). | - |
| US-21 | Mentor ziet wekelijks logboeken | OK | `GET /internships/{id}/logbooks` beschikbaar voor mentor. | Mentor logboek-tabel met validate-knoppen. | - |
| US-22 | Mentor tekent logboeken af | PART | `PATCH /logbooks/{id}` met `mentor_validated=true`. | "Valideren" knop per logboek rij in mentor view. | Geen dedicated sign-off endpoint. Mentor gebruikt een generieke update met een specifiek veld. |

## Fase 5: Evaluatie

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-09 | Student raadpleegt eindevaluatierapport | BUG | Backend route voor `final-report` is staff-only, terwijl de student UI het scherm wel probeert te laden. | Frontend verwacht `report.rules` en `weighted_average_score`, maar backend levert `final_evaluation` en `weighted_final_score`. | End-to-end pad werkt momenteel niet voor studenten. |
| US-18 | Docent vult finale evaluatie in met score per competentie | BUG | `POST /internships/evaluations` + `PATCH /internships/evaluations/{id}/rules/{rule_id}` + `POST /internships/evaluations/{id}/finalize` bestaan. | Frontend/API-client roept `/evaluations/...` zonder `/internships` prefix aan; opslaan/finaliseren faalt in de browser. | Backend bestaat, maar de UI route mismatch breekt de flow. |
| US-19 | Docent genereert eindoverzicht per student | BUG | `GET /internships/{id}/final-report` bestaat. | De docent-view leest de verkeerde response shape en gebruikt dezelfde foutieve mapping als de student-view. | Rapport kan niet correct gerenderd worden in de huidige frontend. |
| US-23 | Mentor geeft feedback per competentie | BUG | Zelfde endpoint als US-16; mentor toegang via `require_any_staff`. | Mentor view gebruikt dezelfde foutieve `/evaluations/...` route en kan feedback daardoor niet betrouwbaar opslaan. | Backend werkt, frontend pad is gebroken. |

## Configuratie & Beheer

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-25 | Administratie beheert competenties en gewichten | PART | Volledige CRUD: CompetencyProfile + Competency endpoints. Gewichten-validatie (som = 100%). Actief/inactief toggelen. | Admin competentiebeheer: toevoegen, verwijderen, gewichten zien, score simulator. | Geen versiebeheer of snapshotting; `Internship` bewaart geen `competency_profile_id`. |
| US-27 | Administratie beheert gebruikers | BE-OK | Volledige CRUD: `GET /users`, `GET /users/{id}`, `POST /users`, `PATCH /users/{id}`, `DELETE /users/{id}`. Alleen admin toegang. | Geen admin UI voor gebruikersbeheer. | Backend compleet; frontend moet nog een admin scherm krijgen. |
| US-28 | Administratie exporteert rapportages | NOK | Rapportage endpoints retourneren JSON. | Geen export UI (download CSV/XLSX/PDF knoppen). | Geen CSV/XLSX/PDF export. Zie `feature-todo.md` item 5. |

## Overkoepelend

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-29 | Gebruiker krijgt melding bij relevante wijziging | NOK | Geen notificatie-infrastructuur. | Geen notificatie UI (bell, badge, toast bij wijziging). | Geen e-mail, push, in-app, websocket of event queue. |

---

## Samenvatting per Status

| Status | Aantal |
|--------|--------|
| OK | 15 |
| BE-OK | 1 |
| PART | 7 |
| BUG | 0 |
| NOK | 3 |

## Top prioriteiten (gesorteerd)

1. **US-29 + US-20 (NOK)** - Notificatiesysteem implementeren
2. **US-09 + US-18 + US-19 + US-23 (BUG)** - Evaluatie- en final-report route/response mismatch in frontend oplossen
3. **US-25 (PART)** - Competency snapshots/versioning toevoegen zodat historische evaluaties stabiel blijven
4. **US-28 (NOK)** - Export rapportages (CSV/XLSX/PDF)
5. **US-01 (PART)** - Stagevoorstel-formulier uitbreiden met docent/mentor selectie
6. **US-27 (BE-OK)** - Admin UI voor gebruikersbeheer (frontend)
