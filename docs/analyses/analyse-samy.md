# 1. Probleemanalyse

## Wat is het probleem?

Op dit moment wordt het stageproces binnen de opleiding op veel verschillende manieren bijgehouden. Er wordt gewerkt met e-mails, Excel-bestanden, en verschillende platformen. Dit zorgt ervoor dat:

- Informatie verspreid staat en moeilijk terug te vinden is
- Niemand een duidelijk overzicht heeft van waar een stage zich bevindt in het proces
- Communicatie tussen studenten, docenten en bedrijven traag en rommelig verloopt
- Belangrijke documenten zoals stageovereenkomsten (nodig voor de verzekering) soms verloren gaan of te laat worden ingediend
- Als de opleiding iets wil veranderen aan de evaluatiecriteria, dit overal manueel moet worden aangepast

## Wat is de oplossing?

Wij gaan een webapplicatie bouwen die het volledige stageproces van begin tot einde ondersteunt. In deze tool kan alles op één centrale plek gebeuren: van het indienen van een stagevoorstel, tot de uiteindelijke evaluatie.

## Wie gebruikt de applicatie?

Er zijn 5 soorten gebruikers:

- **Student** – dient stage in, vult logboeken in, bekijkt evaluaties
- **Stagecommissie** – keurt stagevoorstellen goed of af
- **EhB-docent** – volgt studenten op tijdens de stage en evalueert
- **Stagementor (bedrijf)** – begeleidt de student op de werkvloer, vinkt logboeken af
- **Administratie** – beheert stageovereenkomsten en documenten

## Wat moet de applicatie kunnen?

De belangrijkste functionaliteiten zijn:

- Stagevoorstel indienen en laten beoordelen door de commissie
- Stageovereenkomst uploaden en opvolgen
- Wekelijks logboek bijhouden tijdens de stage
- Evaluaties invullen op basis van competenties (die aanpasbaar moeten zijn)
- Tussentijdse en finale evaluatie met scores en feedback
- Eindoverzicht genereren per student

---

## 2. User Stories

Hieronder staan onze user stories. We gebruiken het formaat: Als [rol], wil ik [wat], zodat [waarom].

| ID | Rol | Ik wil... | Zodat... |
|----|-----|-----------|----------|
| US-01 | Student | een stagevoorstel indienen met de gegevens van het bedrijf, de opdracht en de periode | de stagecommissie mijn voorstel kan bekijken en beoordelen |
| US-02 | Student | kunnen zien wat de status is van mijn stagevoorstel | ik weet of het goedgekeurd is of niet |
| US-03 | Student | feedback krijgen als mijn voorstel aangepast moet worden | ik weet wat ik moet veranderen |
| US-04 | Stagecommissie | alle ingediende voorstellen in een lijst zien | ik ze makkelijk kan overlopen |
| US-05 | Stagecommissie | een voorstel goedkeuren, afkeuren of terugsturen met feedback | studenten weten of ze verder kunnen |
| US-06 | Student | mijn stageovereenkomst uploaden na goedkeuring | de administratie het document kan controleren |
| US-07 | Administratie | zien welke studenten hun overeenkomst al hebben ingediend | ik kan opvolgen of alle papieren in orde zijn |
| US-08 | Student | wekelijks een logboek invullen met wat ik gedaan heb, een reflectie en eventuele problemen | mijn werk tijdens de stage gedocumenteerd wordt |
| US-09 | EhB-docent | de logboeken van mijn studenten kunnen lezen | ik hun voortgang kan opvolgen |
| US-10 | Stagementor | het logboek van mijn student per week afvinken | ik bevestig dat de beschreven taken kloppen |
| US-11 | Admin | competenties kunnen toevoegen, aanpassen en verwijderen | de evaluatie altijd up-to-date is met het huidige beleid |
| US-12 | EhB-docent | per competentie een score geven aan een student | de evaluatie gestructureerd verloopt |
| US-13 | Student | per competentie beschrijven wat ik geleerd heb | ik kan aantonen wat mijn vorderingen zijn |
| US-14 | EhB-docent | feedback geven per competentie | de student weet waar die nog aan moet werken |
| US-15 | EhB-docent | een tussentijdse evaluatie kunnen doen met feedback | problemen vroeg opgemerkt worden |
| US-16 | EhB-docent | een finale evaluatie invullen met scores op alle competenties | het eindresultaat van de student officieel vastgelegd is |
| US-17 | EhB-docent | een eindoverzicht per student kunnen bekijken/genereren | ik een compleet rapport heb |
| US-18 | Student | mijn eindresultaat kunnen bekijken met alle scores en feedback | ik weet hoe ik beoordeeld ben |
| US-19 | Admin | gebruikers en hun rollen kunnen beheren | alleen de juiste mensen toegang hebben tot de juiste functies |
| US-20 | Alle gebruikers | een melding krijgen als er iets verandert dat mij aangaat | ik altijd op de hoogte ben |

---

## 3. Acceptatiecriteria

Hieronder beschrijven we wanneer we een user story als "klaar" beschouwen. Dit zijn de voorwaarden waaraan voldaan moet zijn.

### Algemeen (geldt voor alles)

- De code werkt zonder errors
- Het is getest (manueel of met tests)
- De code is op GitHub gezet via een pull request

### US-01: Stagevoorstel indienen

- Er is een formulier met velden voor bedrijf, contactpersoon, opdracht, en stageperiode
- Alle verplichte velden moeten ingevuld zijn anders krijg je een foutmelding
- Na indienen krijgt het voorstel de status "Ingediend"
- Het voorstel verschijnt in de lijst van de stagecommissie

### US-05: Voorstel beoordelen

- De commissie kan een voorstel openen en de details bekijken
- Er zijn 3 knoppen: Goedkeuren, Afkeuren, Aanpassingen vereist
- Bij "Aanpassingen vereist" moet feedback ingevuld worden
- De student kan de nieuwe status zien

### US-06: Overeenkomst uploaden

- Upload is alleen mogelijk als het voorstel goedgekeurd is
- Alleen PDF-bestanden worden geaccepteerd
- De administratie kan het document bekijken en markeren als ontvangen of onvolledig

### US-08: Logboek invullen

- De student ziet een lijst van alle weken van de stageperiode
- Per week kan je taken, reflectie en problemen/leerpunten invullen
- Je kan opslaan als concept of definitief indienen
- De mentor kan het logboek afvinken

### US-11: Competenties beheren

- Admin kan competenties toevoegen met een naam, beschrijving en gewicht
- Competenties kunnen aangepast en verwijderd worden
- Competenties zijn NIET hardgecodeerd in de code
- Oude evaluaties blijven werken als competenties veranderen

### US-16: Finale evaluatie

- Alle competenties worden getoond met een veld om een score in te vullen
- De eindscore wordt automatisch berekend op basis van de gewichten
- De docent kan feedback geven per competentie
- Na afronden kan de evaluatie niet meer gewijzigd worden

---

## 4. Software Architectuur

### Hoe is de applicatie opgebouwd?

Onze applicatie bestaat uit 3 lagen:

#### Frontend (wat de gebruiker ziet)

- Gebouwd met React
- De gebruiker opent de app in de browser
- Afhankelijk van je rol (student, docent, ...) zie je een ander dashboard

#### Backend / API (de logica)

- Gebouwd met Node.js + Express
- Verwerkt alle aanvragen van de frontend
- Controleert wie je bent en wat je mag doen (authenticatie + autorisatie)
- Bevat de regels, bv: je kan pas een overeenkomst uploaden als je voorstel goedgekeurd is

#### Database (waar de data staat)

- TBD; persoonlijk voorkeur PostgreSQL
- Slaat alle gegevens op: gebruikers, voorstellen, logboeken, evaluaties, ...

#### Bestandsopslag

- Geüploade bestanden (stageovereenkomsten) worden apart opgeslagen

### Belangrijke ontwerpkeuzes

- Competenties worden opgeslagen in de database, niet in de code. Zo kan een admin ze makkelijk aanpassen zonder dat wij iets moeten programmeren.
- Elke gebruiker heeft een rol (student, docent, mentor, admin, ...). Wat je kan doen hangt af van je rol.
- De frontend en backend zijn los van elkaar. Ze communiceren via een API (REST).

### Use Cases

Hieronder een overzicht van wat elke gebruiker kan doen:

| Gebruiker | Wat kan deze gebruiker? |
|-----------|-------------------------|
| **Student** | Stagevoorstel indienen en aanpassen, Overeenkomst uploaden, Logboek invullen, Vorderingen beschrijven, Eindresultaat bekijken |
| **Stagecommissie** | Voorstellen bekijken en beoordelen, Feedback geven |
| **EhB-docent** | Logboeken lezen, Tussentijdse evaluatie doen, Finale evaluatie invullen, Eindrapport genereren |
| **Stagementor** | Logboeken bekijken en afvinken, Feedback geven |
| **Administratie** | Overeenkomsten opvolgen, Overzichten bekijken |
| **Admin** | Competenties beheren, Gebruikers en rollen beheren |

---

## 5. Datamodel

Hieronder staat een overzicht van de tabellen in onze database. Per tabel geven we de belangrijkste kolommen.

### Tabel: users

| Kolom | Uitleg |
|-------|--------|
| id | Unieke ID (primary key) |
| email | E-mailadres |
| password | Wachtwoord (gehasht) |
| first_name, last_name | Naam |
| role | student / commission / teacher / mentor / admin |

### Tabel: internship_proposals

| Kolom | Uitleg |
|-------|--------|
| id | Unieke ID |
| student_id | Verwijst naar users |
| company_name | Naam van het bedrijf |
| contact_person, contact_email | Contactgegevens bedrijf |
| assignment_description | Omschrijving van de opdracht |
| start_date, end_date | Stageperiode |
| status | submitted / approved / rejected / revision_required |
| feedback | Feedback van de commissie (als er aanpassingen nodig zijn) |

### Tabel: internship_agreements

| Kolom | Uitleg |
|-------|--------|
| id | Unieke ID |
| proposal_id | Verwijst naar internship_proposals |
| file_url | Link naar het geüploade bestand |
| status | uploaded / received / incomplete / verified |

### Tabel: weekly_logs

| Kolom | Uitleg |
|-------|--------|
| id | Unieke ID |
| proposal_id | Verwijst naar internship_proposals |
| week_number | Weeknummer |
| tasks_description | Wat heb ik gedaan deze week |
| reflection | Reflectie |
| issues_learnings | Problemen of leerpunten |
| status | draft / submitted / confirmed |

### Tabel: competencies

| Kolom | Uitleg |
|-------|--------|
| id | Unieke ID |
| name | Naam van de competentie |
| description | Uitleg |
| weight | Gewicht (hoe zwaar telt deze mee) |
| academic_year | Academiejaar (bv. 2025-2026) |
| is_active | Actief of niet |

### Tabel: evaluations

| Kolom | Uitleg |
|-------|--------|
| id | Unieke ID |
| proposal_id | Verwijst naar internship_proposals |
| type | interim (tussentijds) / final (einde) |
| evaluator_id | Wie evalueert (verwijst naar users) |
| status | draft / finalized |

### Tabel: evaluation_scores

| Kolom | Uitleg |
|-------|--------|
| id | Unieke ID |
| evaluation_id | Verwijst naar evaluations |
| competency_id | Verwijst naar competencies |
| score | De score |
| student_description | Wat de student zelf schrijft over deze competentie |
| evaluator_feedback | Feedback van de docent/mentor |

### Relaties tussen tabellen

- Een user (student) kan meerdere internship_proposals hebben
- Een internship_proposal heeft maximaal 1 internship_agreement
- Een internship_proposal heeft meerdere weekly_logs (1 per week)
- Een internship_proposal kan meerdere evaluations hebben (tussentijds + finaal)
- Een evaluation heeft meerdere evaluation_scores (1 per competentie)

---

## 6. Schema's en Diagrammen

Hieronder beschrijven we de belangrijkste flows van de applicatie.

### Hoofdflow: het stageproces

Het volledige proces verloopt als volgt:

1. Student dient een stagevoorstel in
2. Stagecommissie beoordeelt het voorstel
   - Goedgekeurd: student mag overeenkomst uploaden
   - Afgekeurd: student krijgt bericht met reden
   - Aanpassingen nodig: student past aan en dient opnieuw in
3. Administratie controleert de overeenkomst
4. Stage start: student vult wekelijks logboek in
5. Mentor vinkt logboeken af, docent volgt op
6. Tussentijdse evaluatie (optioneel)
7. Finale evaluatie met scores op alle competenties
8. Eindoverzicht wordt gegenereerd

### Goedkeuringsflow

De flow voor het beoordelen van een stagevoorstel:

- Student dient in → status wordt "Ingediend"
- Commissie bekijkt het voorstel
- Keuze 1: Goedkeuren → status "Goedgekeurd" → overeenkomst-upload wordt mogelijk
- Keuze 2: Afkeuren → status "Afgekeurd" → student krijgt melding
- Keuze 3: Aanpassingen → status "Revisie vereist" → student kan aanpassen en opnieuw indienen

### Evaluatieflow

- Het systeem haalt de actieve competenties op
- De docent/mentor vult per competentie een score in
- De student kan per competentie beschrijven wat die geleerd heeft
- De docent geeft feedback per competentie
- De gewogen eindscore wordt automatisch berekend

---

## 7. Prototype

We maken een klikbaar prototype in Figma. Hieronder staan de schermen die we gaan uitwerken:

| Scherm | Wat zie je? |
|--------|------------|
| Loginpagina | Simpel inlogscherm met e-mail en wachtwoord |
| Student Dashboard | Overzicht van je stage: status voorstel, logboeken, evaluaties |
| Stagevoorstel formulier | Formulier om een nieuw voorstel in te dienen |
| Commissie overzicht | Lijst van alle ingediende voorstellen met knoppen om te beoordelen |
| Logboek overzicht | Lijst van alle weken met de status per week |
| Logboek invullen | Formulier om een weeklogboek in te vullen |
| Evaluatiescherm | Lijst van competenties met score-invoer en feedbackvelden |
| Eindoverzicht student | Pagina met alle scores, feedback en totaalresultaat |
| Admin: competenties beheren | Scherm om competenties toe te voegen, aan te passen of te verwijderen |

Link naar prototype: TBD

---

## 8. Groepswerking

### Hoe werken we samen?

We werken met Trello om onze taken bij te houden. We hebben een bord met de kolommen: To Do, Bezig, Review, en Klaar.

Voor de code gebruiken we GitHub. Iedereen werkt op een eigen branch en maakt een pull request als iets klaar is. Een ander teamlid kijkt de code na voor het gemerged wordt.

We communiceren via Teams voor dagelijkse afspraken/vragen of maken een Discord aan.

### Taakverdeling

(In te vullen door het team)

| Naam | Rol | Verantwoordelijk voor |
|------|-----|----------------------|
| [Naam 1] | [bv. Frontend] | [bv. React UI, prototype] |
| [Naam 2] | [bv. Backend] | [bv. API, database] |
| [Naam 3] | [bv. Backend] | [bv. Evaluatie module] |
| [Naam 4] | [bv. Full-stack] | [bv. Auth, logboeken] |

### GitHub afspraken

- main branch = werkende code, hier pushen we niet rechtstreeks op
- Iedereen maakt een eigen branch per feature (bv. feature/logboek)
- Pull requests worden nagekeken door minstens 1 teamlid
- We gebruiken duidelijke commit messages
