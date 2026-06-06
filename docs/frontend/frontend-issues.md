# Frontend Probleemoverzicht

Datum: 6 juni 2026 (laatst bijgewerkt: 6 juni 2026, 19:30)
Bron: https://stage-monitoring-demo.fly.dev
Audit gebaseerd op: design-taste-frontend richtlijnen (algemene UI principes)

> **Update:** Dit document is bijgewerkt na de frontend werkzaamheden van 6 juni 2026. Alle opgeloste items zijn gemarkeerd met ✅. Nog openstaande items zijn gemarkeerd met ❌ of ⚠️.

---

## Inhoudsopgave

1. [Kritieke bugs](#1-kritieke-bugs)
2. [Designfouten](#2-designfouten)
3. [Prestatieproblemen](#3-prestatieproblemen)
4. [Kleinere verbeteringen](#4-kleinere-verbeteringen)

---

## 1. Kritieke bugs

### 1.1 Foutmelding "Internship not found" op student-weergaven

**Status:** ✅ **OPGELOST**

**Huidig gedrag:** tabs Dashboard, Voorstel, Logboek, Overeenkomst en Evaluaties tonen een roze banner met de tekst "Fout bij laden: Internship not found".

**Gevolg:** Student kan geen enkele functie gebruiken. De applicatie is onbruikbaar voor deze gebruiker.

**Mogelijke oorzaak:** API retourneert geen geldige internship ID voor deze gebruiker, of de frontend verstuurt een ongeldige request.

**Oplossing geïmplementeerd:**
- `renderStudentDashboard()` toont nu een "Geen stage gevonden" empty state met een bruikbare CTA-knop naar het Voorstel-tabblad
- Geen roze foutbanner meer voor studenten zonder stage

**Bestanden:** `js/views/student.js`

---

### 1.2 Foutmelding toont "[object Object]" bij mislukte login

**Status:** ✅ **OPGELOST**

**Huidig gedrag:** wanneer de snel-login niet lukt, verschijnt "[object Object],[object Object]" als foutmelding.

**Gevolg:** Gebruiker begrijpt niet wat er misgaat.

**Oplossing geïmplementeerd:**
- `formatError()` helper toegevoegd in `js/api-client.js` die FastAPI `detail` arrays (validatiefouten) correct omzet naar leesbare strings
- `AuthAPI.login()` en `apiRequest()` gebruiken nu `formatError()` voor alle foutmeldingen

**Bestanden:** `js/api-client.js`, `js/app.js`

---

## 2. Designfouten

### 2.1 Achtergrond te decoratief voor een beheertool

**Status:** ⚠️ **GEDEELTELIJK OPGELOST**

**Huidig gedrag:** de pagina heeft een gradient-achtergrond met een zichtbaar rasterpatroon (30px grid via de `.ambient` class).

**Probleem:** het raster creëert visuele ruis achter tabellen en formulieren. Een onderwijsbeheertool moet neutraal en overzichtelijk zijn.

**Oplossing geïmplementeerd:**
- Google Fonts link verwijderd uit `index.html` (vermindert externe afhankelijkheden)
- Fonts worden nu lokaal gehost in `fonts/` met `@font-face` declaraties en `font-display: swap`
- Login-pagina krijgt nu `body.login-active { background: #ffffff; }` (neutrale achtergrond)

**Nog open:** `.ambient` raster en `body` gradient zijn nog aanwezig in `styles.css`. Verwijder `.ambient` uit `index.html` en vereenvoudig `body` background voor een volledig neutraal ontwerp.

**Bestanden:** `styles.css`, `index.html`

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

**Status:** ❌ **NOG OPEN**

**Huidig gedrag:** de `.hero` class geeft een roze tint (#fff8f5) en een roze rand.

**Probleem:** deze kaart toont basisgegevens (bedrijf, periode, status). Een roze achtergrond suggereert urgentie of een waarschuwing, wat niet klopt.

**Oplossingsstap:**
- Verwijder de roze achtergrond en rand
- Gebruik dezelfde styling als andere kaarten: `background: #ffffff; border: 1px solid var(--border);`

**Bestanden:** `styles.css` (regel `.hero`)

---

### 2.4 Meldingbell heeft geen hover-staat op lichte achtergrond

**Status:** ❌ **NOG OPEN**

**Huidig gedrag:** `.notif-bell:hover { background: rgba(255, 255, 255, 0.12); }` is onzichtbaar op de lichte achtergrond.

**Oplossingsstap:**
- Vervang door: `background: rgba(18, 38, 58, 0.06);`
- Of gebruik: `background: var(--border);`

**Bestanden:** `styles.css` (regel `.notif-bell:hover`)

---

### 2.5 Inconsistente spatiëring tussen header-elementen

**Status:** ❌ **NOG OPEN**

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

**Status:** ✅ **OPGELOST**

**Huidig gedrag:** in `index.html` staat een `<link>` tag naar Google Fonts CDN.

**Probleem:** render-blokkerend, extra DNS-resolutie, privacy-implicaties (verzoeken naar derde partij).

**Oplossing geïmplementeerd:**
- Lettertypen gedownload en lokaal gehost in `fonts/` (Space Grotesk 400/500/700, IBM Plex Sans 400/500/600)
- `@font-face` declaraties met `font-display: swap` toegevoegd in `styles.css`
- Google Fonts `<link>` tags verwijderd uit `index.html`

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

**Status:** ⚠️ **GEDEELTELIJK VERBETERD**

**Huidig gedrag:** als de API niet bereikbaar is, verschijnt er geen melding of een generieke fout.

**Verbeteringen geïmplementeerd:**
- `AuthAPI.demoLogin()` en `AuthAPI.login()` tonen nu specifieke netwerkfoutmeldingen ("Kan geen verbinding maken met de server. Is de backend gestart?")
- `apiRequest()` heeft een 401 redirect guard die dubbele redirects voorkomt

**Nog open:** Geen globale netwerkfoutafhandeling met retry-knop voor alle API calls. Alleen login/demo-login heeft expliciete netwerkfout afhandeling.

**Bestanden:** `js/api-client.js`

---

### 4.3 Tabel-kolomen niet leesbaar op mobiel

**Status:** ⚠️ **GEDEELTELIJK VERBETERD**

**Huidig gedrag:** op schermen smaller dan 720px krijgen tabellen `min-width: 640px` en worden horizontaal scrollbaar. De card-weergave toont niet alle kolommen (bijv. "Acties" met knoppen ontbreekt soms).

**Verbeteringen geïmplementeerd:**
- Mobile CSS verbergt nu alleen tabellen met `[data-table-cards]` attribuut, niet meer ALLE tabellen
- `removeTableCards()` helper toegevoegd om cleanup te verbeteren

**Nog open:** De card-weergave zelf toont nog niet alle relevante kolommen (bijv. "Acties" met knoppen). Tabellen zonder card-alternatief blijven horizontaal scrollbaar.

**Bestanden:** `js/table-cards.js`, `styles.css`

---

### 4.4 Login-pagina is over-design voor een beheertool

**Status:** ✅ **OPGELOST**

**Huidig gedrag:** de login-pagina heeft dezelfde gradient + raster-achtergrond als de rest van de applicatie.

**Oplossing geïmplementeerd:**
- `body.login-active { background: #ffffff; }` toegevoegd — login-pagina heeft nu een neutrale witte achtergrond

**Bestanden:** `styles.css` (regel `.login-layout`)

---

## Samenvatting per bestand

| Bestand | Aantal issues | Opgelost | Nog open |
|---|---|---|---|
| `styles.css` | 7 | 3 (fonts, login-bg, data-table-cards) | 4 (ambient, hero, notif-hover, spacing) |
| `index.html` | 3 | 2 (reveal, fonts) | 1 (ambient raster) |
| `js/api-client.js` | 1 | 1 (formatError + netwerkfouten) | 0 |
| `js/app.js` | 1 | 1 (formatError + 401 guard) | 0 |
| `js/views/student.js` | 2 | 1 (empty state) | 1 (skeleton loader) |
| `js/table-cards.js` | 1 | 0 | 1 (card columns) |

## Aanbevolen volgorde

### Direct uit te voeren (lage moeite, hoge impact)
1. **2.3** `.hero` roze achtergrond verwijderen — 1 regel CSS
2. **2.4** `.notif-bell:hover` fixen — 1 regel CSS
3. **2.5** Spatiëring standaardiseren — 3 regels CSS
4. **2.1** `.ambient` raster verwijderen — 1 regel HTML

### Daarna
5. **4.1** Skeleton loader voor laadstatus
6. **4.3** Card-weergave uitbreiden met actieknoppen
7. **4.2** Globale netwerkfoutafhandeling met retry

### Laatst
8. **2.2** Tab-kleur unificeren (teal als primair)
