# Demo Script: Stage Monitoring Tool

**Doel:** Jury tonen dat alle user stories werken, end-to-end.
**Tijdsduur:** 5-7 minuten.
**Voorbereiding:** `python seed_loader.py` + `uvicorn app.main:app --reload` + `frontend` in browser.

---

## Stap 1: Quick Login - Student (Jan Peeters)

**Actie:** Open de loginpagina. Klik "Jan Peeters (student)" in de quick-login.
**Wat te tonen:**
- Dashboard met "Mijn Stage", status "Lopend" bij DataFlow Solutions
- Logboeken overzicht, 4 weken ingediend, mentor moet nog valideren
- Competentie progressie, tussentijdse evaluatie in concept
- Openstaande taken: "Wacht op mentor validatie week 4"

Jury-boodschap: *"Student ziet direct waar hij staat. Progress is glanceable."*

---

## Stap 2: Student - Nieuw stagevoorstel indienen

**Actie:** Log uit → quick-login "Marie Verhoeven (student)".
**Wat te tonen:**
- Tab "Voorstel" → formulier met bedrijfsgegevens, periode, beschrijving
- Docent dropdown laadt beschikbare docenten (API call)
- Vul een dummy voorstel in → indienen

Jury-boodschap: *"Student dient zelf in. Validatie op verplichte velden."*

---

## Stap 3: Commissie - Voorstel beoordelen

**Actie:** Log uit → quick-login "Peter Smit (commissie)".
**Wat te tonen:**
- Tab "Voorstellen", tabel met alle voorstellen
- Marie's voorstel staat bovenaan ("Ingediend")
- Klik op de rij → detail paneel opent
- Klik "In Beoordeling" → dan "Goedkeuren" + feedback typen
- Klik opbouw: "De commissie beoordeelt in twee stappen. Eerst 'In Beoordeling', dan de beslissing."

Jury-boodschap: *"Commissie heeft controle, kan goedkeuren, afkeuren, of aanpassingen vragen."*

---

## Stap 4: Student - Overeenkomst uploaden

**Actie:** Log uit → quick-login "Marie Verhoeven".
**Wat te tonen:**
- Status op dashboard: "Goedgekeurd"
- Tab "Overeenkomst" → upload PDF (pick any .pdf file)
- Status wijzigt naar "Overeenkomst Ingediend"

Jury-boodschap: *"Stageovereenkomst is cruciaal voor verzekering. PDF wordt opgeslagen."*

---

## Stap 5: Commissie - Overeenkomst valideren

**Actie:** Log uit → quick-login "Peter Smit".
**Wat te tonen:**
- Tab "Overeenkomsten", Marie's PDF staat in de lijst
- Klik "Bekijken" → PDF preview/download
- Vinkje "Verzekering in orde" → klik "Valideren"
- Status wijzigt naar "Lopend"

Jury-boodschap: *"Commissie controleert verzekering. Status gaat naar 'Lopend', student kan starten."*

---

## Stap 6: Student - Logboek invullen

**Actie:** Log uit → quick-login "Marie Verhoeven".
**Wat te tonen:**
- Status: "Lopend"
- Tab "Logboek", week grid (groen = ingediend, oranje = concept, grijs = ontbrekend)
- Klik week 1 → vul taken, reflectie, problemen → "Opslaan als Concept"
- Klik week 1 opnieuw → "Definitief Indienen"
- Week 1 wordt groen in het grid

Jury-boodschap: *"Wekelijkse opvolging. Student houdt eigen reflectie bij."*

---

## Stap 7: Mentor - Logboek valideren

**Actie:** Log uit → quick-login "Sofie De Vries (mentor)".
**Wat te tonen:**
- Dropdown: kies Marie's stage
- Tab "Validatie", logboek week 1 staat met taken/reflectie
- Klik "Valideren" → status wijzigt, Marie krijgt notificatie

Jury-boodschap: *"Stagementor bevestigt wekelijkse aanwezigheid. Traceerbaar."*

---

## Stap 8: Docent - Evaluatie invullen

**Actie:** Log uit → quick-login "Ann Claessens (docent)".
**Wat te tonen:**
- Dropdown: kies Marie's stage
- Tab "Evaluatie" → type "tussentijds"
- Per competentie: score 1-5, algemene opmerkingen
- "Opslaan als Concept" → dan "Definitief Afsluiten"
- Student krijgt notificatie

Jury-boodschap: *"Evaluatie op basis van competenties. Gewichten zijn configureerbaar."*

---

## Stap 9: Student - Eindoverzicht

**Actie:** Log uit → quick-login "Jan Peeters".
**Wat te tonen:**
- Tab "Evaluaties" → scroll naar eindoverzicht
- Afgeronde stage (TechCorp) met finale score, logboekstatistieken, evaluaties
- "PDF Download" knop voor eindrapport

Jury-boodschap: *"Compleet eindoverzicht per student. PDF voor administratie."*

---

## Stap 10: Admin - Competentiebeheer + Audit Log

**Actie:** Log uit → quick-login "Systeem Beheerder (admin)".
**Wat te tonen:**
- Tab "Competenties", toon actief profiel, gewichten, score simulator
- "Profielen Beheren", maak nieuw profiel aan voor volgend jaar
- Tab "Audit Log", filter op actie, datum, gebruiker
- Elke beslissing is traceerbaar

Jury-boodschap: *"Wendbaar: competenties wijzigen zonder codewijziging. Audit trail voor compliance."*

---

## Stap 11: Admin - Begeleiding wijzigen + stage stopzetten

**Actie:** Blijf ingelogd als "Systeem Beheerder (admin)" (of gebruik commissie).
**Wat te tonen:**
- Tab "Overeenkomsten" → klik "Bekijken" bij een lopende stage
- Onderaan: paneel "Begeleiding wijzigen" met de huidige docent/mentor al voorgeselecteerd
- Wissel de mentor (of docent) → "Wijzigingen opslaan" → toast bevestigt, de nieuwe begeleider krijgt een notificatie
- Klik daarna "Stage stopzetten" → vul een reden in (bv. "Student stopt met de opleiding") → bevestig
- Status wordt rood "Stopgezet"; student, mentor en docent krijgen een melding
- Tab "Audit Log" → toon de events `internship.reassign_mentor` en `internship.terminate` met reden

Jury-boodschap: *"De opleiding kan tijdens een lopende stage ingrijpen wanneer de opvolging wijzigt of de stage abrupt anders verloopt — alles getraceerd en met notificaties."*

---

## Slot - Samenvatting

"Dit is een volledig end-to-end stage monitoring tool. Van voorstel tot evaluatie, met 5 rollen, audit logging, notificaties, en configureerbare competenties. Alle user stories zijn geïmplementeerd, inclusief het wendbaar wijzigen van de begeleiding en het vroegtijdig stopzetten van een stage."

---

## Vangnet: als iets misgaat

| Scenario | Wat te doen |
|----------|-------------|
| Seed data mist | `python seed_loader.py` |
| API start niet | `uvicorn app.main:app --reload` |
| CORS error | `FRONTEND_ORIGINS=*` in `.env` |
| Browser cache | `Ctrl+Shift+R` (hard refresh) |
| Demo te lang | Skip stap 2 (nieuw voorstel), gebruik bestaande data |

---

## Accounts (Quick Login)

| Rol | Email | Wachtwoord |
|-----|-------|-----------|
| Student (afgerond) | `student1@school.be` | `student123` |
| Student (lopend) | `student2@school.be` | `student123` |
| Docent | `docent1@school.be` | `docent123` |
| Commissie | `commissie1@school.be` | `commissie123` |
| Mentor (TechCorp) | `b.janssens@techcorp.be` | `mentor123` |
| Mentor (DataFlow) | `s.devries@dataflow.be` | `mentor123` |
| Admin | `admin@school.be` | `demo123` |
