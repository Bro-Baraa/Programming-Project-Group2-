# User Stories Overzicht - Stagetool Groep 2

Bron: `analyse-finaal.md` x codebase audit
Datum: 2026-06-06

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
| US-01 | Student dient stagevoorstel in met bedrijfs- en opdrachtgegevens | OK | `POST /internships` maakt Internship + Company + Proposal in een keer. `teacher_id`/`mentor_id` worden ondersteund met validatie. | `student.js` laadt `teacher-select` en `mentor-select` dropdowns via `UsersAPI.list('teacher')` / `UsersAPI.list('mentor')`. | Backend en frontend ondersteunen beide de selectie en validatie. |
| US-02 | Student bekijkt status stagevoorstel | OK | `GET /internships/{id}`, `GET /internships/{id}/proposal`, `GET /me/dashboard` retourneren status. | Dashboard toont status-pill; proposal status zichtbaar in detail. | - |
| US-10 | Commissie ziet lijst voorstellen | OK | `GET /internships` retourneert stages met `proposal_status`, zoeken, filteren en paginatie. | Tabel met sorteerbare rijen; overzichtelijke weergave student + bedrijf + status. | - |
| US-24 | Mentor ziet stagecontext | OK | `GET /internships/{id}` toont context; rol-gefilterde toegang. | Stage-selector dropdown; mentor ziet alleen stages waar `mentor_id` op hem staat. | - |

## Fase 2: Beoordeling

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-03 | Student ontvangt feedback bij afkeuring of aanpassingen | OK | `Proposal.feedback` is beschikbaar via `GET /proposal`. `notify()` wordt aangeroepen bij elke beslissing. | Feedback wordt getoond in student dashboard; notificatiebell toont melding. | Notificatie bevat alleen status, niet de volledige feedbacktekst. |
| US-11 | Commissie keurt goed, af, of vraagt aanpassingen | OK | `PATCH /internships/{id}/proposal` met `review_proposal()`. | Reviewscherm ondersteunt eerst "In Beoordeling" zetten, daarna een beslissing. | Twee-staps reviewflow werkt nu in UI en backend. |
| US-12 | Commissie geeft feedback mee bij beslissing | OK | `feedback` is verplicht bij "Aanpassingen Vereist". | Feedback textarea bij review panel. | - |
| US-20 | Docent ontvangt notificatie bij nieuwe logboeken | PART | Notificatie-infrastructuur is volledig (`Notification` model, `/notifications` endpoints, `notify()` helper). | Notificatiebell UI bestaat. | Alleen mentor wordt genotificeerd bij logboek-indiening; docent nog niet. |

## Fase 3: Overeenkomst

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-04 | Student uploadt stageovereenkomst | OK | `POST /internships/{id}/agreement` accepteert PDF; content-type validatie op `application/pdf`; status wijzigt naar "Overeenkomst Ingediend". | Upload formulier met file picker + PDF accept attribuut. | — |
| US-13 | Commissie controleert of overeenkomst is opgeladen | OK | `GET /agreement` toont status. `PATCH /agreement` markeert als "Gevalideerd" of "Onvolledig". | Commissie heeft "Overeenkomsten" tab met lijst, PDF download, verzekeringscheckbox, en validatieknoppen. | — |
| US-26 | Administratie ziet welke studenten overeenkomst hebben ingediend | OK | `GET /internships/reports/agreements` geeft agreement-status. | Admin overzicht (`renderAdminAgreements()`) toont tabel met student, status, agreement_status, datum en detailpaneel. | - |

## Fase 4: Opvolging

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-05 | Student vult wekelijks logboek in met taken en reflecties | OK | `POST /logbooks` en `PATCH /logbooks/{id}` werken. `POST /logbooks/{id}/submit` voor definitief indienen. Velden: tasks, reflection, issues. | Logboekformulier met "Opslaan als Concept" en "Definitief Indienen". | - |
| US-06 | Student beschrijft per competentie wat hij geleerd heeft | OK | `PATCH /evaluations/{id}/rules/{rule_id}` laat `student_description` opslaan. | `student-self-eval-panel` in `student.js` toont per competentie een textarea met save-knop. | - |
| US-07 | Student leest feedback van docent/mentor | OK | `GET /internships/{id}/feedback` retourneert feedback. | Feedback sectie op student dashboard toont berichten met afzender en datum. | Feedback is generiek (`from_user`, `to_user`, `message`); niet gekoppeld aan een logboek-week. |
| US-08 | Student ziet historiek van logboeken | OK | `GET /internships/{id}/logbooks` en `GET .../logbooks/weeks` bestaan, met "missing" markering. | `renderStudentDashboard()` roept `getLogbookWeeks()` aan en toont `missing` rijen in rood. | - |
| US-14 | Commissie ziet overzicht alle stages en statussen | OK | `GET /internships` en `GET /stats/dashboard`. | Overzichtstabel + statistiekenpaneel met totalen. | - |
| US-15 | Docent ziet wekelijkse logboeken | OK | `GET /internships/{id}/logbooks` beschikbaar voor docent. | Docent logboek-tabel met week, taken, reflectie, status, mentor validatie. | - |
| US-16 | Docent geeft feedback per competentie | OK | `evaluator_feedback` in `EvaluationRule` werkt via PATCH. | Evaluatieformulier heeft feedback veld per competentie. | Gekoppeld aan evaluaties, niet aan logboeken. Geen feedback op specifieke logboek-week. |
| US-17 | Docent registreert tussentijdse evaluatie | OK | `POST /evaluations` met `eval_type: "tussentijds"`. | Evaluatieformulier met type selector (tussentijds/final). | - |
| US-21 | Mentor ziet wekelijks logboeken | OK | `GET /internships/{id}/logbooks` beschikbaar voor mentor. | Mentor logboek-tabel met validate-knoppen. | - |
| US-22 | Mentor tekent logboeken af | OK | `PATCH /logbooks/{id}` met `mentor_validated=true`. | "Valideren" knop per logboek rij in mentor view. | Endpoint is generiek update; voldoet aan requirement. |

## Fase 5: Evaluatie

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-09 | Student raadpleegt eindevaluatierapport | OK | `GET /internships/{id}/final-report` gebruikt `get_current_active_user` + `ensure_internship_access` in service. | Frontend verwacht `final_evaluation` en `weighted_final_score` — backend levert dit correct. | Student kan eigen eindrapport laden. `reports.py` gebruikt `get_current_active_user`, service valideert toegang. |
| US-18 | Docent vult finale evaluatie in met score per competentie | OK | `POST /internships/evaluations` + `PATCH /internships/evaluations/{id}/rules/{rule_id}` + `POST /internships/evaluations/{id}/finalize` bestaan. | Frontend roept correcte routes aan (`/internships/evaluations/...`). | - |
| US-19 | Docent genereert eindoverzicht per student | OK | `GET /internships/{id}/final-report` bestaat. | Docent-view leest `final_evaluation` en `weighted_final_score` correct. | - |
| US-23 | Mentor geeft feedback per competentie | OK | Zelfde endpoint als US-16; mentor toegang via `require_any_staff`. | Mentor view roept correcte `/internships/evaluations/{id}/rules/{rule_id}` route aan. | - |

## Configuratie & Beheer

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-25 | Administratie beheert competenties en gewichten | OK | Volledige CRUD: CompetencyProfile + Competency endpoints. Gewichten-validatie (som = 100%). Actief/inactief toggelen. `Internship.competency_profile_id` kopieert actief profiel bij aanmaak. | Admin competentiebeheer: toevoegen, verwijderen, gewichten zien, score simulator. | Profiel wordt gekopieerd naar stage bij aanmaak; historische stages ongewijzigd bij profielwijziging. Evaluaties gebruiken stage-profiel. |
| US-27 | Administratie beheert gebruikers | OK | Volledige CRUD: `GET /users`, `GET /users/{id}`, `POST /users`, `PATCH /users/{id}`, `DELETE /users/{id}`. Alleen admin toegang. | Admin UI bestaat (`admin-gebruikers-template`); `renderUserManager()` in `admin.js` implementeert volledige CRUD met zoeken, paginatie, en formulier. | - |
| US-28 | Administratie exporteert rapportages | NOK | Rapportage endpoints retourneren JSON. Geen export dependencies (`openpyxl`, `reportlab`). Geen export endpoints (`/reports/export/excel`, `/{id}/export/pdf`). | Geen export UI (download CSV/XLSX/PDF knoppen). | **Ontbrekend:** (1) backend dependencies `openpyxl` + `reportlab`, (2) export service `services/export.py`, (3) endpoints voor Excel (admin dashboard) en PDF (eindrapport), (4) frontend API client methoden, (5) download knoppen in admin/student views. |

## Overkoepelend

| ID | User Story | Status | Backend | Frontend | Opmerkingen |
|----|-----------|--------|---------|----------|-------------|
| US-29 | Gebruiker krijgt melding bij relevante wijziging | PART | Notificatie-infrastructuur is volledig: `Notification` model, `/notifications` endpoints, `notify()` helper, frontend bell met polling. | Notificatie UI (bell, badge, dropdown) is volledig geïmplementeerd. | Ontbrekende triggers: (1) feedback aangemaakt → ontvanger, (2) evaluatie gefinaliseerd → student, (3) docent bij logboek-indiening. |

---

## Samenvatting per Status

| Status | Aantal |
|--------|--------|
| OK | 26 |
| BE-OK | 0 |
| PART | 2 |
| BUG | 0 |
| NOK | 1 |

## Top prioriteiten (gesorteerd)

1. **US-28 (NOK)** - Export rapportages (CSV/XLSX/PDF)
2. **US-20 (PART)** - Docent notificatie bij logboek-indiening: `teacher_id` toevoegen in `logbooks.py` naast `mentor_id`
3. **US-29 (PART)** - Ontbrekende notificatietriggers: (a) feedback aangemaakt in `feedback.py`, (b) evaluatie gefinaliseerd in `evaluations.py`
