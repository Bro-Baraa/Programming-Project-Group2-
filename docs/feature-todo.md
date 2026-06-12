# Feature TODO - Ontbrekende Onderdelen

Dit document bevat de features die nog moeten worden geïmplementeerd om de requirements uit `analyse-finaal.md` volledig te ondersteunen.

## Huidige status

**Laatst bijgewerkt:** 6 juni 2026 — verificatie uitgevoerd tegen codebase.

### Reeds geïmplementeerd

| Feature | Status | Bewijs |
|---------|--------|--------|
| **Logboek "missing" weken** | ✅ Volledig | Backend: `logbooks.py`, `dashboard.py`, `report_final.py`. Frontend: `student.js`, `mentor.js`, `teacher.js` tonen `Ontbrekend` |
| **Proposal herindiening MVP** | ✅ Volledig | `models.py`: `revision_count` + `resubmitted_at`. `lifecycle.py`: counter. `student.js`: toont in UI |
| **Final report / eindoverzicht** | ✅ Volledig | `services/report_final.py` met stage-info, logboekstatistieken, evaluatie, weighted score |
| **Dashboard aggregatie** | ✅ Volledig | `services/dashboard.py` met `joinedload`, alerts, logboek-math, evaluatie-samenvatting |
| **Audit Logging** | ✅ Volledig | `models.py`: `AuditLog`. `services/audit.py`: `log_event()`. `routers/audit.py`: admin endpoints. Triggers in `logbooks.py`, `lifecycle.py` |
| **Notificatiesysteem** | ✅ Volledig | `models.py`: `Notification`. `services/notifications.py`: `notify()`. `routers/notifications.py`: CRUD. Frontend: `notifications.js` bell-icoontje + dropdown. Triggers in `lifecycle.py` |
| **Competentieprofiel koppelen aan Stage** | ✅ Volledig | `models.py`: `Internship.competency_profile_id`. `lifecycle.py`: kopieert actief profiel bij stage-aanmaak. `evaluations.py`: gebruikt stage-profiel, niet systeem-default. Historische stages ongewijzigd bij profielwijziging |
| **"Ontbrekend" status Logboeken (frontend)** | ✅ Volledig | Frontend: `student.js`, `mentor.js`, `teacher.js` renderen `missing`-weeks met `status-warn` / `status-missing` CSS. `index.html` legenda aanwezig |

### Echt nog ontbrekend

Geen features meer ontbrekend. Alle requirements uit `analyse-finaal.md` zijn geïmplementeerd.

| Feature | Status | Impact |
|---------|--------|--------|
| **Export functionaliteit (CSV)** | ✅ Geïmplementeerd | `GET /internships/reports/export/csv` retourneert UTF-8 CSV. Frontend: download knop in admin overeenkomsten-view. |

---

## Prioriteit: Hoog

### 1. Audit Logging
**Status:** ✅ Volledig geïmplementeerd
**Requirement:** *"Alle statuswijzigingen, evaluaties en documentacties worden geaudit (tijdstip + actor)"*
**Gerelateerde user stories:** [US-29](#user-stories-overzicht)

**Implementatie bewijs:**
- **Model:** `backend/app/models.py` heeft `AuditLog` met `id`, `actor_id`, `action`, `entity_type`, `entity_id`, `old_value`, `new_value`, `timestamp`, `ip_address`
- **Service:** `backend/app/services/audit.py` met `log_event()` helper
- **Router:** `backend/app/routers/audit.py` met admin endpoints voor filtering
- **Triggers:** `backend/app/routers/logbooks.py` en `backend/app/services/lifecycle.py` roepen `log_event()` aan bij statuswijzigingen, evaluaties, uploads
- **Frontend:** Admin kan audit logs bekijken per stage

**Acceptatiecriteria:**
- [x] Elke statuswijziging van een stage wordt gelogd
- [x] Elke evaluatie-afronding wordt gelogd
- [x] Elke overeenkomst-upload wordt gelogd
- [x] Admin kan audit logs filteren per stage en per gebruiker
- [x] Audit logs zijn alleen-lezen en kunnen niet worden verwijderd

---

### 2. Notificatiesysteem
**Status:** ✅ Volledig geïmplementeerd
**Requirements:** [US-20](#user-stories-overzicht), [US-29](#user-stories-overzicht)

**Implementatie bewijs:**
- **Model:** `backend/app/models.py` heeft `Notification` met `id`, `user_id`, `message`, `internship_id`, `link_view`, `is_read`, `created_at`
- **Service:** `backend/app/services/notifications.py` met `notify()` helper
- **Router:** `backend/app/routers/notifications.py` met endpoints:
  - `GET /notifications` — lijst notificaties
  - `PATCH /notifications/{id}/read` — markeer als gelezen
  - `PATCH /notifications/read-all` — markeer alles gelezen
- **Frontend:** `frontend/js/notifications.js` met bell-icoontje, dropdown, auto-polling (30s)
- **Frontend:** `frontend/index.html` heeft notificatie UI elementen
- **Triggers:** `backend/app/services/lifecycle.py` stuurt notificaties bij:
  - Nieuw stagevoorstel ingediend → commissie
  - Voorstel beoordeeld → student
  - Overeenkomst gevalideerd → student
  - Logboek ingediend → mentor
  - Evaluatie afgerond → student

**Acceptatiecriteria:**
- [x] Student krijgt notificatie als voorstel wordt beoordeeld
- [x] Docent krijgt notificatie als student logboek indient
- [x] Student krijgt notificatie als feedback wordt gegeven
- [x] Gebruiker kan notificaties als "gelezen" markeren
- [x] Notificaties worden getoond in chronologische volgorde
- [ ] (Optioneel) E-mail wordt verstuurd bij belangrijke wijzigingen

---

### Reeds geïmplementeerd (branch `feature/proposal-versiegeschiedenis`)

| Feature | Status | Bewijs |
|---------|--------|--------|
| **Proposal versiegeschiedenis (volledig)** | ✅ Volledig | `models.py`: `Proposal.version` + `Proposal.revised_at`. `ProposalVersion` tabel. `lifecycle.py`: `edit_proposal` + `resubmit_proposal` bewaren oude versies. `proposals.py`: `GET /{id}/proposal/versions` endpoint. `student.js`: toont versie + laatst bewerkt. |

---

## Prioriteit: Medium

### 3. Versiegeschiedenis voor Proposals
**Status:** ✅ Volledig geïmplementeerd
**Requirement:** *"Student kan aanpassen en opnieuw indienen"* bij status "Aanpassingen vereist"
**Gerelateerde user stories:** [US-01](#user-stories-overzicht), [US-11](#user-stories-overzicht)

**Implementatie bewijs:**
- **Model:** `backend/app/models.py` heeft `Proposal.version` (integer, default 1) en `Proposal.revised_at` (datetime, nullable)
- **Model:** `backend/app/models.py` heeft `ProposalVersion` tabel met `id`, `proposal_id`, `version`, `description`, `status`, `feedback`, `submitted_at`, `resubmitted_at`, `created_at`
- **Service:** `backend/app/services/lifecycle.py`: `edit_proposal` en `resubmit_proposal` slaan oude versie op in `ProposalVersion` vooraleer te updaten, incrementeren `version`, zetten `revised_at`
- **Router:** `backend/app/routers/proposals.py`: `GET /{internship_id}/proposal/versions` — geeft volledige versiegeschiedenis terug
- **Schema:** `backend/app/schemas/proposal.py`: `ProposalVersionResponse` schema
- **Frontend:** `frontend/js/views/student.js`: toont "Versie X" en "Laatst bewerkt" bij proposal

**Acceptatiecriteria:**
- [x] `Proposal` heeft veld `version` (integer, default 1)
- [x] `Proposal` heeft veld `revised_at` (datetime, nullable)
- [x] Bij elke wijziging: oude versie wordt opgeslagen in `ProposalVersion` tabel
- [x] Bij elke herindiening: version +1, revised_at = now()
- [x] Admin kan historiek bekijken via `GET /{internship_id}/proposal/versions`
- [x] Frontend toont "Versie X" bij proposal bekijken

---

## Prioriteit: Laag

### 4. Export Functionaliteit (CSV)
**Status:** ✅ Geïmplementeerd
**Requirement:** *"rapportages exporteren zodat data bruikbaar is voor rapportering"*
**Gerelateerde user stories:** [US-28](#user-stories-overzicht)

**Huidige stand:**
- CSV export endpoint: `GET /internships/reports/export/csv` — retourneert UTF-8 CSV met BOM voor Excel-compatibiliteit
- Frontend: "Exporteer CSV" knop in admin overeenkomsten-view
- PDF eindrapport bestaat: `GET /internships/{id}/final-report/pdf` (gegenereerd met `fpdf2`)

**Acceptatiecriteria:**
- [x] Admin kan stage-overzicht exporteren naar CSV
- [x] CSV bevat alle relevante data (student, bedrijf, status, docent, mentor, voorstel- en overeenkomst-status)
- [x] PDF eindrapport beschikbaar per student

---

## Samenvatting: Wat Moet Eerst?

| Volgorde | Feature | Status | Reden |
|----------|---------|--------|-------|
| 1 | **Audit Logging** | ✅ Done | Vereist voor traceerbaarheid en auditbaar gedrag |
| 2 | **Notificatiesysteem** | ✅ Done | Veel user stories verwachten dit (US-20, US-29) |
| 3 | **Competentieprofiel koppeling** | ✅ Done | Voorkomt data-inconsistentie bij profielwijzigingen |
| 4 | **Logboek "ontbrekend"** | ✅ Done | UI verbetering; backend + frontend compleet |
| 5 | **Proposal versiegeschiedenis** | ✅ Done | Herindiening werkt + volledige historiek in `ProposalVersion` tabel |
| 6 | **Export functionaliteit** | ✅ Done | CSV export voor admin; PDF eindrapport voor student/docent |

---

**Status:** Alle features geïmplementeerd. Project is klaar voor indiening/demo.
