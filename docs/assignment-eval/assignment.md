# PROJECTCASE: Ontwikkeling van een Stage Monitoring Tool

## 1. Context

Binnen de opleiding worden studenten verplicht een stage te volgen. Het volledige stageproces – van aanvraag tot eindevaluatie – wordt vandaag deels manueel en via verschillende platformen opgevolgd. Dit zorgt voor versnippering, beperkte transparantie en inefficiëntie in communicatie tussen student, stagecommissie, docent en bedrijf.

De opleiding wenst daarom een digitale tool te laten ontwikkelen die het volledige stageproces ondersteunt en monitort. Deze applicatie moet flexibel, schaalbaar en eenvoudig aanpasbaar zijn, zodat wijzigingen in het evaluatiebeleid of de stageprocedure snel kunnen worden doorgevoerd.

**Jullie opdracht is om een applicatie te ontwerpen en te bouwen die dit proces end-to-end ondersteunt.**

---

## 2. Doel van de Applicatie

De applicatie moet dienen als centrale stage monitoring tool voor:

- **Studenten**
- **Stagecommissie**
- **EhB-docenten** (die de studenten opvolgen)
- **Stagementoren** binnen het bedrijf
- **Administratie**

De tool moet:

1. Het stageaanvraagproces structureren
2. De goedkeuringsflow ondersteunen
3. Documenten en overeenkomsten beheren
4. Wekelijkse opvolging mogelijk maken
5. Evaluaties en scoring faciliteren
6. Flexibel omgaan met wijzigende evaluatiecriteria

---

## 3. Overzicht van het Stageproces

### Fase 1: Indienen van een stagevoorstel

De student dient een stage in via de applicatie. De volgende gegevens moeten minimaal ingevoerd worden:

- Gegevens van de student, bedrijf, docent, enz.
- Omschrijving van de opdracht
- Periode van de stage

De stage krijgt de status **"Ingediend, wachtend op goedkeuring"**.

---

### Fase 2: Beoordeling door de stagecommissie

De stagecommissie beoordeelt de aanvraag. Mogelijke beslissingen:

- **Goedgekeurd**
- **Afgekeurd**
- **Aanpassingen vereist** (met feedback)

---

### Fase 3: Stageovereenkomst

Na goedkeuring moet een stageovereenkomst worden opgeladen en geregistreerd.

> **Belangrijk:** De stageovereenkomst is cruciaal voor de verzekering en moet correct ondertekend zijn.

---

### Fase 4: Stageopvolging via wekelijkse logboeken

Tijdens de stage moet de student wekelijks een logboek invullen. In elk logboek:

- Beschrijving van uitgevoerde taken
- Reflectie
- Eventuele problemen of leerpunten

Deze logboeken moeten:

- Ingekeken kunnen worden door de EhB-docent
- Ingekeken kunnen worden door het bedrijf
- Wekelijks afgecheckt worden door de stagementor

---

### Fase 5: Evaluatie

De evaluatie gebeurt op basis van competenties.

> **Belangrijk:** Competenties zijn editeerbaar. Ze kunnen wijzigen in aantal, inhoud en gewicht. De applicatie mag dus **geen hardgecodeerde evaluatiestructuur** hebben.

Per competentie moet:

- Een score toegekend kunnen worden
- De student een beschrijving kunnen geven van zijn/haar vorderingen
- De docent of mentor feedback kunnen geven

> **Competenties:** In het geval van Toegepaste Informatica vind je de competenties hier.

#### Tussentijdse Bespreking

Er moet een mogelijkheid zijn om een tussentijdse evaluatie of bespreking te registreren. Dit kan bestaan uit:

- Feedbackmoment
- Scoring (optioneel)

#### Finale Evaluatie

Op het einde van de stage:

- Eindpresentatie
- Finale scoring
- Definitieve evaluatie op competenties

De applicatie moet een **eindoverzicht** kunnen genereren per student.

---

## 4. Belangrijke Vereiste: Wendbaarheid

De opleiding moet snel kunnen inspelen op beleidswijzigingen. Competentieprofielen kunnen veranderen, de stage-opvolging kan wijzigen of plots anders verlopen. **Zorg dat de software snel kan inspelen op veranderingen.**
