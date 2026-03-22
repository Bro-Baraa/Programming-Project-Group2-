# Stage Monitoring Tool Probleemanalyse

Het stageproces speelt een belangrijke rol binnen de opleiding, omdat studenten via hun stage praktijkervaring opdoen en begeleid worden door verschillende partijen zoals docenten en bedrijven.

In de huidige situatie verloopt dit proces niet op een uniforme manier. Verschillende onderdelen, zoals communicatie, documenten en opvolging, zijn verspreid over meerdere tools of worden manueel uitgevoerd. Hierdoor ontstaat er geen duidelijk totaaloverzicht van de stage.

Dit maakt het voor alle betrokken partijen moeilijk om het proces efficiënt te volgen en tijdig in te grijpen wanneer nodig.

Om dit probleem op te lossen, is er nood aan een centrale applicatie die het volledige stageproces bundelt en een duidelijk overzicht biedt van alle stappen, documenten en evaluaties.


---

## 1. User Stories

| ID | Rol | Functionaliteit | User Story |
|----|-----|-----------------|-------------|
| US1 | Student | Stagevoorstel indienen | Als student wil ik een stagevoorstel indienen zodat de stagecommissie mijn stage kan bekijken en goedkeuren |
| US2 | Student | Stagevoorstel indienen | Als student wil ik een stageovereenkomst uploaden zodat mijn stage officieel geregistreerd wordt. |
| US3 | Student | Logboeken invullen | Als student wil ik wekelijkse logboeken invullen zodat docenten en mentoren mijn voortgang kunnen volgen. |
| US4 | Student | Evaluaties bekijken | Als student wil ik mijn evaluaties bekijken zodat ik kan zien hoe mijn stage verloopt en wat ik kan verbeteren. |
| US5 | Stagecommissie | Stagevoorstellen beoordelen | Als lid van de stagecommissie wil ik stagevoorstellen bekijken en beoordelen zodat ik kan beslissen of een stage wordt goedgekeurd of niet. |
| US6 | Docent | Logboeken opvolgen | Als docent wil ik de logboeken van studenten bekijken zodat ik de voortgang van de student kan opvolgen. |
| US7 | Docent | Evaluatie geven | Als docent wil ik feedback en evaluaties geven zodat de student kan verbeteren tijdens de stage. |
| US8 | Stagementor | Logboeken controleren | Als stagementor wil ik wekelijkse logboeken bekijken zodat ik kan controleren wat de student gedaan heeft. |
| US9 | Stagementor | Feedback geven | Als stagementor wil ik een evaluatie en feedback geven zodat de competenties van de student beoordeeld kunnen worden. |
| US10 | Administratie | Competenties beheren | Als administrator wil ik competenties beheren zodat de evaluatiecriteria aangepast kunnen worden wanneer nodig. |

---

## 2. Backlog

- Het systeem moet een login functie hebben zodat gebruikers veilig kunnen inloggen.
- Studenten moeten een stagevoorstel kunnen indienen met informatie over het bedrijf, de stageperiode en een beschrijving van de opdracht.
- De stagecommissie moet stagevoorstellen kunnen bekijken en beoordelen, zodat ze een stage kunnen goedkeuren, afkeuren of aanpassingen vragen.
- Na goedkeuring moet de student een stageovereenkomst kunnen uploaden, zodat de stage officieel geregistreerd wordt.
- Tijdens de stage moeten studenten wekelijkse logboeken kunnen invullen waarin ze hun taken, reflecties en eventuele problemen beschrijven.
- Docenten en stagementoren moeten logboeken kunnen bekijken, zodat ze de voortgang van de student kunnen opvolgen.
- Het systeem moet een evaluatiesysteem op basis van competenties hebben, zodat docenten en mentoren de student kunnen beoordelen.
- Administratie moet competenties kunnen beheren, zodat het aantal competenties en hun gewicht aangepast kan worden wanneer nodig.
- Op het einde van de stage moet het systeem een eindoverzicht van de evaluatie kunnen genereren voor elke student.

---

## 3. Acceptatiecriteria (Definition of Done)

### Stagevoorstel indienen

Deze functie is klaar wanneer:

- De student een stagevoorstel kan invullen
- Bedrijfsinformatie kan toegevoegd worden
- De periode van de stage kan ingevoerd worden
- De beschrijving van de stage kan toegevoegd worden
- De status wordt "Ingediend"

### Logboek

Deze functie is klaar wanneer:

- Studenten een wekelijks logboek kunnen schrijven
- Taken en reflectie kunnen toevoegen
- Mentoren het logboek kunnen bekijken
- Docenten het logboek kunnen bekijken

### Evaluatie van stage

Deze functie is klaar wanneer:

- Competenties gekozen kunnen worden
- Een score gegeven kan worden
- Feedback kan toegevoegd worden

---

## 4. Schema's

1. **ER-diagram** – toont de structuur van de database

```mermaid
erDiagram
    STUDENT {
        int id
        string name
        string email
    }

    INTERNSHIP {
        int id
        string company
        string period
    }

    LOGBOOK {
        int id
        string content
        date week
    }

    EVALUATION {
        int id
        int score
        string feedback
    }

    STUDENT ||--o{ INTERNSHIP : submits
    INTERNSHIP ||--o{ LOGBOOK : contains
    STUDENT ||--o{ LOGBOOK : writes
    INTERNSHIP ||--o{ EVALUATION : has
   
3. **Use Case diagram** – toont wat gebruikers in het systeem kunnen doen
4. **Activity diagram** – toont het verloop van het stageproces
5. **Architectuur diagram** – toont hoe het systeem technisch opgebouwd is

---

## 5. Prototype

Er werd een prototype uitgewerkt om een eerste beeld te geven van hoe de applicatie eruit zal zien en hoe gebruikers ermee zullen werken.

Het prototype toont de belangrijkste schermen van het systeem en maakt het mogelijk om de structuur, navigatie en gebruiksvriendelijkheid van de applicatie beter te begrijpen.

Op deze manier kan in een vroege fase gecontroleerd worden of de opbouw van het systeem logisch en duidelijk is voor alle gebruikers.

De belangrijkste pagina's in het prototype zijn:

| Pagina | Beschrijving |
|--------|-------------|
| Loginpagina | Gebruikers kunnen hier inloggen met hun accountgegevens om toegang te krijgen tot het systeem. |
| Dashboard voor studenten | Deze pagina geeft een overzicht van de stage zoals de status van het stagevoorstel en belangrijke meldingen. |
| Stagevoorstel formulier | Via dit formulier kan een student een stagevoorstel indienen met informatie over het bedrijf, de stageperiode en de stageopdracht. |
| Logboekpagina | Op deze pagina kunnen studenten wekelijkse logboeken invullen en kunnen docenten of mentoren deze opvolgen. |
| Evaluatiepagina | Hier kunnen docenten en stagementoren evaluaties uitvoeren en feedback geven op basis van de competenties. |
| Eindoverzicht van de stage | Deze pagina toont een overzicht van de evaluaties en de uiteindelijke beoordeling van de student. |

Het prototype dient als visuele voorbereiding voor de ontwikkeling van de applicatie en helpt bij het verduidelijken van de functionaliteiten en de interactie tussen gebruikers en het systeem.

---

## 6. Groepswerking

Tijdens het project wordt er in team gewerkt. GitHub wordt gebruikt voor het beheren van de code en version control. Trello wordt gebruikt om taken te organiseren en de voortgang van het project op te volgen. De taken worden verdeeld tussen de teamleden zodat iedereen weet waarvoor hij verantwoordelijk is.
