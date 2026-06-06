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

### Echt nog ontbrekend

| Feature | Status | Impact |
|---------|--------|--------|
| **Competentieprofiel koppelen aan Stage** | ❌ Niet geïmplementeerd | `internships` tabel heeft geen `competency_profile_id` |
| **Proposal versiegeschiedenis (volledig)** | ❌ Niet geïmplementeerd | Alleen MVP-counter, geen `ProposalVersion` tabel |
| **Export functionaliteit** | ❌ Niet geïmplementeerd | Geen `openpyxl`, `reportlab`, of export endpoints |

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

## Prioriteit: Medium

### 3. Competentieprofiel Koppelen aan Stage
**Status:** Gedeeltelijk: profiel wordt opgehaald, maar niet opgeslagen op stage-niveau  
**Requirement:** *"Wijzigingen gelden enkel voor nieuwe stageperiodes; historische evaluaties blijven ongewijzigd"*  
**Gerelateerde user stories:** [US-25](#user-stories-overzicht)

**Probleem:** Als een admin het actieve competentieprofiel wijzigt, gebruiken lopende stages meteen het nieuwe profiel. Dat mag niet.

**Wat moet er gebeuren:**
- `Internship` model uitbreiden met `competency_profile_id`
- Bij aanmaken van stage: kopieer het dan-actieve profiel ID
- Bij evaluatie: gebruik altijd het profiel gekoppeld aan de stage, niet het "huidige actieve profiel"

**Acceptatiecriteria:**
- [ ] `Internship` heeft veld `competency_profile_id`
- [ ] Bij aanmaken stage wordt profiel ID opgeslagen
- [ ] Evaluaties gebruiken het profiel van de stage, niet het systeem-default
- [ ] Oude stages blijven het oude profiel gebruiken ook als admin wijzigt

**Impact:**
- Database migratie nodig (nieuw veld)
- Backend: aanpassen waar evaluaties worden aangemaakt
- Frontend: geen wijzigingen

---

### 4. Versiegeschiedenis voor Proposals
**Status:** Gedeeltelijk (MVP-counter aanwezig, volledige historiek niet)  
**Requirement:** *"Student kan aanpassen en opnieuw indienen"* bij status "Aanpassingen vereist"  
**Gerelateerde user stories:** [US-01](#user-stories-overzicht), [US-11](#user-stories-overzicht)

**Huidige stand:**
- `Proposal` heeft al `revision_count` en `resubmitted_at`.
- De student kan na "Aanpassingen Vereist" opnieuw indienen.
- Er is nog geen echte versiehistoriek of vergelijking tussen versies.

**Vraag:** Willen we oude versies bewaren of alleen de laatste?

**Optie A (simpel):** Overschrijven
- Student past proposal aan, oude versie gaat verloren
- Veld `version` bijhouden (1, 2, 3...)
- Veld `revised_at` bijhouden

**Optie B (compleet):** Volledige historiek
- Nieuwe tabel `ProposalVersion`
- Elke wijziging slaat een nieuwe rij op
- Admin kan alle versies vergelijken

**Aanbeveling:** Optie A voor MVP, Optie B als later vereist.

**Acceptatiecriteria (Optie A):**
- [ ] `Proposal` heeft veld `version` (integer, default 1)
- [ ] `Proposal` heeft veld `revised_at` (datetime, nullable)
- [ ] Bij elke herindiening: version +1, revised_at = now()
- [ ] Frontend toont "Versie X" bij proposal bekijken

**Acceptatiecriteria (Optie B):**
- [ ] Nieuwe tabel `ProposalVersion` met volledige kopie
- [ ] Bij wijziging: oude versie wordt opgeslagen in `ProposalVersion`
- [ ] Admin kan historiek bekijken en vergelijken

---

## Prioriteit: Laag

### 5. Export Functionaliteit (Rapporten)
**Status:** Niet geïmplementeerd  
**Requirement:** *"rapportages exporteren zodat data bruikbaar is voor rapportering"*  
**Gerelateerde user stories:** [US-28](#user-stories-overzicht)

**Wat moet er gebeuren:**
- Excel export voor admin/dashboard data
- PDF export voor eindrapporten (mooi geformatteerd)
- Backend endpoints toevoegen `/internships/reports/export`

**Technologie opties:**
- **Excel:** `openpyxl` (Python library)
- **PDF:** `reportlab` of `WeasyPrint` (HTML -> PDF)

**Acceptatiecriteria:**
- [ ] Admin kan dashboard data exporteren naar Excel
- [ ] Student/docent kan eindrapport exporteren naar PDF
- [ ] Export bevat alle relevante data (stage info, logboeken, evaluaties, scores)

---

### 6. "Ontbrekend" Status voor Logboeken
**Status:** Gedeeltelijk: backend berekent missing-weken, frontend toont ze nog niet  
**Requirement:** *"Niet-ingevulde weken gemarkeerd als 'Ontbrekend'"*  
**Gerelateerde user stories:** [US-08](#user-stories-overzicht)

**Opmerking:** Dit is geen database wijziging, maar frontend logica. De backend heeft al een week-overzicht en `missing` status.

**Wat moet er gebeuren:**
- Frontend toont lijst van alle weken in de stageperiode
- Voor elke week: check of er een `Logbook` bestaat
- Zo nee: toon "Ontbrekend" (rood/oranje markeren)

**Acceptatiecriteria:**
- [ ] Student ziet voor elke week of logboek is ingevuld, ontbrekend, of nog toekomstig
- [ ] Ontbrekende weken zijn visueel duidelijk (bijv. rood/oranje)
- [ ] Docent/mentor ziet welke studenten ontbrekende logboeken hebben

---

## Samenvatting: Wat Moet Eerst?

| Volgorde | Feature | Reden |
|----------|---------|-------|
| 1 | **Audit Logging** | Vereist voor traceerbaarheid en auditbaar gedrag |
| 2 | **Notificatiesysteem** | Veel user stories verwachten dit (US-20, US-29) |
| 3 | **Competentieprofiel koppeling** | Voorkomt data-inconsistentie bij profielwijzigingen |
| 4 | **Proposal versiegeschiedenis** | Nodig voor volledige herindiening flow |
| 5 | **Export functionaliteit** | Rapportage-eis voor administratie |
| 6 | **Logboek "ontbrekend"** | UI verbetering; backend bestaat al grotendeels |
