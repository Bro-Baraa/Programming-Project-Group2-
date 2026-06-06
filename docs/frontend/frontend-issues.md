# Frontend Probleemoverzicht

Datum: 6 juni 2026
Bron: https://stage-monitoring-demo.fly.dev
Audit gebaseerd op: design-taste-frontend richtlijnen (algemene UI principes)

---

## Inhoudsopgave

1. [Kritieke bugs](#1-kritieke-bugs)
2. [Designfouten](#2-designfouten)
3. [Prestatieproblemen](#3-prestatieproblemen)
4. [Kleinere verbeteringen](#4-kleinere-verbeteringen)

---

## 1. Kritieke bugs

### 1.1 Foutmelding "Internship not found" op student-weergaven

**Huidig gedrag:** tabs Dashboard, Voorstel, Logboek, Overeenkomst en Evaluaties tonen een roze banner met de tekst "Fout bij laden: Internship not found".

**Gevolg:** Student kan geen enkele functie gebruiken. De applicatie is onbruikbaar voor deze gebruiker.

**Mogelijke oorzaak:** API retourneert geen geldige internship ID voor deze gebruiker, of de frontend verstuurt een ongeldige request.

**Oplossingsstap:**
- Controleer of de API een geldig internship object retourneert voor de ingelogde student
- Vervang de foutbanner door een bruikbare empty state met instructie (bijv. "Je hebt nog geen stage ingediend. Dien een voorstel in via het tabblad Voorstel.")
- Voeg een retry-knop toe bij nettwerkfouten

**Bestanden:** `js/views/student.js`

---

### 1.2 Foutmelding toont "[object Object]" bij mislukte login

**Huidig gedrag:** wanneer de snel-login niet lukt, verschijnt "[object Object],[object Object]" als foutmelding.

**Gevolg:** Gebruiker begrijpt niet wat er misgaat.

**Oplossingsstap:**
- Parseer het foutobject voordat het wordt weergegeven
- Toon een leesbaar bericht (bijv. "Inloggen mislukt. Controleer je gegevens.")

**Bestanden:** `js/app.js` (waarschijnlijk in de login-handler)

---

## 2. Designfouten

### 2.1 Achtergrond te decoratief voor een beheertool

**Huidig gedrag:** de pagina heeft een gradient-achtergrond met een zichtbaar rasterpatroon (30px grid via de `.ambient` class).

**Probleem:** het raster creëert visuele ruis achter tabellen en formulieren. Een onderwijsbeheertool moet neutraal en overzichtelijk zijn.

**Oplossingsstap:**
- Verwijder de `.ambient` class uit `index.html`
- Vervang de gradient in `body` door een enkele vlakke kleur: `background: #f4f0e6;`
- Optioneel: voeg een subtieler tint toe met `background: linear-gradient(180deg, #f4f0e6 0%, #f6fbff 100%);`

**Bestanden:** `styles.css` (regel `.ambient` en `body`)

---

### 2.2 Actieve tab gebruikt verkeerde accentkleur

**Huidig gedrag:** actieve navigatietabs zijn roze/rood (`var(--accent)`, #c73d50). Primaire actieknoppen zijn teal (`var(--accent-2)`, #00798c).

**Probleem:** de gebruiker weet niet welke kleur "primair" betekent. Tabs en knoppen communiceren verschillende dingen met dezelfde visuele intensiteit.

**Oplossingsstap:**
- Kies één primaire kleur voor alle interactieve elementen
- Aanbeveling: gebruik teal (`var(--accent-2)`) als primaire kleur voor tabs én knoppen
- Gebruik roze (`var(--accent)`) alleen voor destructieve acties (verwijderen, afkeuren)
- Pas `.nav-tab.active` aan in `styles.css`

**Bestanden:** `styles.css` (regel `.nav-tab.active`)

---

### 2.3 "Mijn Stage" kaart heeft roze achtergrond

**Huidig gedrag:** de `.hero` class geeft een roze tint (#fff8f5) en een roze rand.

**Probleem:** deze kaart toont basisgegevens (bedrijf, periode, status). Een roze achtergrond suggereert urgentie of een waarschuwing, wat niet klopt.

**Oplossingsstap:**
- Verwijder de roze achtergrond en rand
- Gebruik dezelfde styling als andere kaarten: `background: #ffffff; border: 1px solid var(--border);`

**Bestanden:** `styles.css` (regel `.hero`)

---

### 2.4 Meldingbell heeft geen hover-staat op lichte achtergrond

**Huidig gedrag:** `.notif-bell:hover { background: rgba(255, 255, 255, 0.12); }` is onzichtbaar op de lichte achtergrond.

**Oplossingsstap:**
- Vervang door: `background: rgba(18, 38, 58, 0.06);`
- Of gebruik: `background: var(--border);`

**Bestanden:** `styles.css` (regel `.notif-bell:hover`)

---

### 2.5 Inconsistente spatiëring tussen header-elementen

**Huidig gedrag:**
- Topbar: `padding: 1.4rem 1rem 0.8rem`
- Nav: `padding: 0.8rem 1rem 0`
- Content: `padding: 0.8rem 1rem 1.2rem`

**Probreem:** de waarden zijn geen veelvouden van een basiseenheid, wat zorgt voor onregelmatige rhythm.

**Oplossingsstap:**
- Kies een basiseenheid van 8px (0.5rem)
- Standaardiseer: topbar `padding: 1rem 1rem 0.5rem`, nav `padding: 0.5rem 1rem 0`, content `padding: 0.5rem 1rem 1rem`

**Bestanden:** `styles.css`

---

## 3. Prestatieproblemen

### 3.1 Google Fonts via `<link>` geladen

**Huidig gedrag:** in `index.html` staat een `<link>` tag naar Google Fonts CDN.

**Probleem:** render-blokkerend, extra DNS-resolutie, privacy-implicaties (verzoeken naar derde partij).

**Oplossingsstap:**
- Download de lettertypen (Space Grotesk 400/500/700, IBM Plex Sans 400/500/600)
- Host ze lokaal in `fonts/` map
- Gebruik `@font-face` declaraties met `font-display: swap`
- Verwijder de `<link>` tags uit `index.html`

**Bestanden:** `index.html`, `styles.css` (nieuwe `@font-face` regels)

---

### 3.2 Onnodige `.reveal` animaties op elk panel

**Huidig gedrag:** elk `.panel` element heeft een `animation: rise 420ms ease both` entry-animatie.

**Probleem:** bij het wisselen van tabs worden alle elementen opnieuw geanimeerd. Dit vertraagt de perceptie van snelheid voor herhaald gebruik.

**Oplossingsstap:**
- Verwijder `.reveal` class uit alle templates in `index.html`
- Of beperk de animatie tot alleen de eerste page load (niet bij tab-wissel)

**Bestanden:** `index.html` (templates), `styles.css` (regel `.reveal`)

---

## 4. Kleinere verbeteringen

### 4.1 Laadstatus toont alleen "Gegevens laden..."

**Huidig gedrag:** de "Openstaande Taken" kaart toont een enkele tekstregel als laadstatus.

**Aanbeveling:** vervang door een skeleton-loader die de vorm van de uiteindelijke inhoud nabootst (bijv. 3 grijze balkjes voor een lijst).

**Bestanden:** `js/views/student.js`

---

### 4.2 Geen foutafhandeling bij nettwerkproblemen

**Huidig gedrag:** als de API niet bereikbaar is, verschijnt er geen melding of een generieke fout.

**Aanbeveling:**
- Voeg een globale foutafhandeling toe die nettwerkfouten herkent
- Toon een melding met een retry-knop
- Onderscheid tussen "geen verbinding" en "serverfout"

**Bestanden:** `js/api-client.js`

---

### 4.3 Tabel-kolomen niet leesbaar op mobiel

**Huidig gedrag:** op schermen smaller dan 720px krijgen tabellen `min-width: 640px` en worden horizontaal scrollbaar. De card-weergave toont niet alle kolommen (bijv. "Acties" met knoppen ontbreekt soms).

**Aanbeveling:** zorg ervoor dat de card-weergave alle relevante kolommen bevat, inclusief actieknoppen.

**Bestanden:** `js/table-cards.js`

---

### 4.4 Login-pagina is over-design voor een beheertool

**Huidig gedrag:** de login-pagina heeft dezelfde gradient + raster-achtergrond als de rest van de applicatie.

**Aanbeveling:** gebruik een neutrale lichte achtergrond voor de login. Een school beoordeelt de tool op professioneel uiterlijk, niet op decoratieve achtergronden.

**Bestanden:** `styles.css` (regel `.login-layout`)

---

## Samenvatting per bestand

| Bestand | Aantal issues |
|---|---|
| `styles.css` | 7 |
| `index.html` | 3 |
| `js/views/student.js` | 2 |
| `js/app.js` | 1 |
| `js/api-client.js` | 1 |
| `js/table-cards.js` | 1 |

## Aanbevolen volgorde

1. Eerst de kritieke bugs (sectie 1) - deze blokkeren het gebruik
2. Dan de designfouten (sectie 2) - deze beïnvloeden de bruikbaarheid
3. Dan prestaties (sectie 3) - nice-to-have
4. Tot slot de kleinere verbeteringen (sectie 4) - polish
