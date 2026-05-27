# Stage Monitoring Tool Prototype

Dit is een klikbaar frontend-prototype op basis van de analyse in analyse-juan-extended.md.

## Starten

Optie 1: open prototype/index.html direct in de browser.

Optie 2 (aanbevolen, lokale server):

```bash
cd prototype
python3 -m http.server 8080
```

Ga dan naar http://localhost:8080.

## Wat zit erin

### Rollen
- **Student**: Dashboard, Stagevoorstel, Logboek, Evaluaties
- **Stagecommissie**: Voorstellen beoordelen
- **Docent**: Opvolging, Evaluatie
- **Stagementor**: Validatie
- **Administratie**: Competentiebeheer

### Functionaliteiten
- **State Machine**: Simpele state machine voor stageflow met transitieregels.
- **Validatieregel**: Overgang naar "Lopend" kan alleen als overeenkomst_getekend=true.
- **Stagevoorstel**: Formulier voor studenten om stagevoorstel in te dienen (met validatie).
- **Logboek**: Wekelijks logboek invullen met taken, reflectie en problemen.
- **Evaluatie**: Docent kan tussentijdse en finale evaluaties invullen met scores per competentie.
- **Competentiebeheer**: Gewichten en controle op totaal = 100%.
- **Finale score**: Gewogen berekening: sum(score * gewicht) / 100.

### Screens per rol

| Rol | Schermen |
|-----|----------|
| Student | Dashboard, Stagevoorstel indienen, Logboek invullen, Evaluaties bekijken |
| Stagecommissie | Voorstellen overzicht + feedback |
| Docent | Missing Logs, Tussentijdse evaluatie, Evaluatie formulier |
| Stagementor | Wekelijkse validatie |
| Administratie | Competentiebeheer + Finale score simulator |

## Focus

Dit prototype is bedoeld voor validatie van UX-flow, rollen en kernlogica.
Het bevat geen backend, authenticatie of persistente opslag.

## Gebaseerd op

- analyse-juan-extended.md (Hoofddocument)
- analyse-juan.md
- analyse-samy.md
- analyse-baraa.md
- analyse-leila.md
- analyse-yorick.md
