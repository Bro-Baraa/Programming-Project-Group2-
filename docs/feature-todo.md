# Feature TODO - Ontbrekende Onderdelen

Dit document bevat de features die nog moeten worden geïmplementeerd om de requirements uit `analyse-finaal.md` volledig te ondersteunen.

## Huidige status

Een aantal punten uit de oorspronkelijke analyse zijn al deels of grotendeels aanwezig in de codebase:

- Proposal herindiening bestaat al als MVP via `revision_count` en `resubmitted_at`.
- Logboek-weken met status `missing` worden al door de backend berekend.
- Competentiebeheer bestaat al, maar historische snapshotting ontbreekt nog.
- De evaluatieflow bestaat in de backend, maar de frontend gebruikt foutieve routes en response shapes.

De items hieronder beschrijven dus niet alleen ontbrekende features, maar ook de resterende hiaten die de requirements nog blokkeren.

## Prioriteit: Hoog

### 1. Audit Logging
**Status:** Niet geïmplementeerd  
**Requirement:** *"Alle statuswijzigingen, evaluaties en documentacties worden geaudit (tijdstip + actor)"*  
**Gerelateerde user stories:** [US-29](#user-stories-overzicht)

**Wat moet er gebeuren:**
- Nieuwe database tabel `AuditLog` aanmaken
- Middleware of service hooks toevoegen om wijzigingen automatisch te loggen
- Frontend: admin scherm om audit logs te bekijken per stage

**Datamodel:**
```
AuditLog:
  - id (primary key)
  - actor_id (wie heeft de actie uitgevoerd, FK naar users)
  - action (wat is er gebeurd: "status_change", "evaluation_finalized", "agreement_uploaded")
  - entity_type (bijv. "internship", "proposal", "evaluation")
  - entity_id (ID van het betreffende object)
  - old_value (optioneel: oude waarde bij wijzigingen)
  - new_value (optioneel: nieuwe waarde)
  - timestamp (wanneer)
  - ip_address (optioneel: voor extra security)
```

**Acceptatiecriteria:**
- [ ] Elke statuswijziging van een stage wordt gelogd
- [ ] Elke evaluatie-afronding wordt gelogd
- [ ] Elke overeenkomst-upload wordt gelogd
- [ ] Admin kan audit logs filteren per stage en per gebruiker
- [ ] Audit logs zijn alleen-lezen en kunnen niet worden verwijderd

---

### 2. Notificatiesysteem
**Status:** Niet geïmplementeerd  
**Requirements:** [US-20](#user-stories-overzicht), [US-29](#user-stories-overzicht)

**Wat moet er gebeuren:**
- Nieuwe database tabel `Notification` aanmaken
- Trigger punten in de code identificeren (waar worden notificaties aangemaakt)
- Frontend: notificatie bell/icoontje in de header
- Optioneel: e-mail integratie (SendGrid, Mailgun)

**Datamodel:**
```
Notification:
  - id (primary key)
  - user_id (ontvanger, FK naar users)
  - type ("logbook_submitted", "proposal_status_changed", "feedback_received", etc.)
  - title (korte titel voor preview)
  - message (volledige bericht)
  - read (boolean, default false)
  - created_at (timestamp)
  - related_entity_type (bijv. "internship", voor deeplink)
  - related_entity_id (ID voor deeplink)
```

**Acceptatiecriteria:**
- [ ] Student krijgt notificatie als voorstel wordt beoordeeld
- [ ] Docent krijgt notificatie als student logboek indient
- [ ] Student krijgt notificatie als feedback wordt gegeven
- [ ] Gebruiker kan notificaties als "gelezen" markeren
- [ ] Notificaties worden getoond in chronologische volgorde
- [ ] (Optioneel) E-mail wordt verstuurd bij belangrijke wijzigingen

**Triggers (waar moet code aangepast worden):**
- Proposal status wijziging -> notificatie naar student
- Logbook indiening -> notificatie naar docent + mentor
- Feedback geplaatst -> notificatie naar ontvanger
- Evaluatie gefinaliseerd -> notificatie naar student

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
