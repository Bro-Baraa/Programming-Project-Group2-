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

- Rolselector: Student, Stagecommissie, Docent, Stagementor, Administratie.
- Simpele state machine voor stageflow met transitieregels.
- Validatieregel: overgang naar "Lopend" kan alleen als overeenkomst_getekend=true.
- Schermsimulaties per rol gebaseerd op wireframes.
- Competentiebeheer met gewichten en controle op totaal = 100%.
- Finale score simulator met gewogen berekening: sum(score * gewicht) / 100.

## Focus

Dit prototype is bedoeld voor validatie van UX-flow, rollen en kernlogica.
Het bevat geen backend, authenticatie of persistente opslag.
