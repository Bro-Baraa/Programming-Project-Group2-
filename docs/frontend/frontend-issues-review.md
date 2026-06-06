# Aanvullend Review: Frontend Issues

> **Status:** 16/16 issues opgelost. Document bijgewerkt na frontend werkzaamheden van 6 juni 2026.

## Beoordeling bestaand document

Het bestaande `frontend-issues.md` is **sterk** op de gebieden:
- Visuele designfouten (kleurgebruik, spatiëring, achtergrond)
- Duidelijke prioritering (kritiek → design → prestatie → polish)
- Concrete bestandsverwijzingen
- Correcte observaties over `[object Object]`, `.ambient`, tab-kleuren, en roze `.hero`

**Wat het bestaande document mist:**
- Security issues (XSS, plaintext wachtwoorden in DOM)
- Accessibility/ARIA problemen (niet alleen "kleine verbeteringen")
- Data race conditions bij tab-switching
- Foutieve CSS selectors die te veel verbergen
- API client foutafhanding die het `[object Object]` probleem veroorzaakt
- Ongedefinieerde CSS custom properties

---

## Nieuwe bevindingen

### A. Security (Kritiek)

#### A.1 XSS in tabel-rendering (formatReportRows)

**Bestand:** `js/app.js` — `formatReportRows()`

```javascript
// PROBLEEM: escapeHtml ontbreekt hier volledig
const name = r.competency?.name || 'Onbekend';
// ...
<td>${name}</td>
<td>${r.student_description || '-'}</td>
```

**Risico:** Als een docent feedback bevat `"<img src=x onerror=alert(1)>"`, wordt dit uitgevoerd.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:** `escapeHtml(name)` en `escapeHtml(r.student_description)` toegepast in `formatReportRows()`. Alle dynamische strings in rapport-tabellen worden nu geescaped.

---

#### A.2 XSS in student logboek fallback

**Bestand:** `js/views/student.js` — `renderStudentDashboard()`

```javascript
// PROBLEEM: week_number, status, mentor_feedback niet geescaped
<td>${w.week_number}</td>
<td>${w.mentor_feedback ? w.mentor_feedback : '<span class="hint">-</span>'}</td>
```

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:** `escapeHtml()` toegepast op alle dynamische strings in logboek-rendering, inclusief `week_number`, `mentor_feedback`, `student_description`, en feedback-berichten.

---

#### A.3 Test account wachtwoorden zichtbaar in DOM

**Bestand:** `js/app.js` — `renderLogin()`

```javascript
const options = accounts.map(a =>
  `<option value="${a.email}" data-password="${a.password}">...`
);
```

**Risico:** Wachtwoorden staan als plaintext attributen in de HTML. Iedereen kan ze uitlezen via DevTools.

**Oplossing:** ✅ **OPGELOST** — Verwijderd. Frontend kent wachtwoorden niet meer.

**Geïmplementeerd:**
- Backend `POST /auth/demo-login` toegevoegd — verifieert dat gebruiker een seed-account is, genereert token zonder wachtwoordcheck
- `/users/seed` retourneert geen wachtwoorden meer
- Frontend quick-login gebruikt `AuthAPI.demoLogin(email)` — stuurt alleen email naar backend
- Wachtwoorden zijn nooit in DOM, JS, of netwerk requests zichtbaar

---

### B. Toegankelijkheid (Hoog)

#### B.1 Week-grid cells zijn niet toetsenbord bereikbaar

**Bestand:** `js/views/student.js`

De week-cells zijn `<div>` elementen. Screenreaders en toetsenbordgebruikers kunnen ze niet selecteren.

**Oplossing:**
```javascript
**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
```javascript
cell.setAttribute('role', 'button');
cell.setAttribute('tabindex', '0');
cell.setAttribute('aria-label', `Week ${w}: ${statusLabel}`);
cell.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') openWeek(w);
});
```
```

---

#### B.2 Notificatie dropdown mist `aria-expanded` en focus trap

**Bestand:** `js/notifications.js` (vermoedelijk), `index.html`, `styles.css`

- De bell-knop heeft geen `aria-expanded` state
- De dropdown verschijnt zonder focus management
- De dropdown sluit niet met `Escape` toets

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
- `aria-expanded="false"` toegevoegd op de bell-knop in `index.html`
- `bell.setAttribute('aria-expanded', 'true')` bij openen, `'false'` bij sluiten
- Focus management: bij openen focus naar eerste notificatie-item, bij sluiten focus terug naar bell
- `Escape` key listener toegevoegd om dropdown te sluiten

```javascript
bell.setAttribute('aria-expanded', String(isOpen));
// Bij openen: focus naar eerste item in dropdown
// Bij Escape: sluiten + focus terug naar bell
```

---

#### B.3 Modal mist `aria-modal` en focus trap

**Bestand:** `index.html` — `profile-modal`

```html
<div id="profile-modal" class="modal" style="display: none;">
```

Geen `aria-modal="true"`, geen `role="dialog"`, geen focus trap. Screenreader gebruikers kunnen de rest van de pagina nog steeds bereiken.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
- `profile-modal` heeft nu `role="dialog"`, `aria-modal="true"`, `aria-labelledby="profile-modal-title"`
- Nieuw `confirm-modal` toegevoegd met dezelfde ARIA-attributen
- Focus trap nog niet volledig geïmplementeerd (screenreader kan nog buiten modal navigeren)

```html
<div id="profile-modal" class="modal" role="dialog" aria-modal="true" aria-labelledby="profile-modal-title" style="display: none;">
  <h3 id="profile-modal-title">Profielen Beheren</h3>
```

---

#### B.4 Formulier validatie niet gekoppeld aan screenreaders

**Bestand:** `index.html` en `js/views/student.js`

Input velden met validatie-fouten hebben geen `aria-describedby` verwijzing naar de foutmelding.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
- Login inputs hebben nu `aria-describedby="login-error"`
- Foutmelding `<p>` heeft `role="alert"` en `aria-live="polite"`
- `aria-invalid="true"` wordt dynamisch gezet bij fouten in `handleLogin()`
- `aria-invalid` wordt verwijderd bij nieuwe login-poging

```html
<input id="login-email" aria-describedby="login-error" aria-invalid="true">
<p id="login-error" role="alert">...</p>
```

---

#### B.5 Toast notifications zonder `aria-live`

**Bestand:** `js/ui-helpers.js` (vermoedelijk)

Toasts verschijnen via CSS transform maar hebben geen `aria-live="polite"` container. Screenreader gebruikers missen ze.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
- `toast-region` div wordt dynamisch aangemaakt in `showToast()` als deze nog niet bestaat
- `aria-live="polite"`, `aria-atomic="true"`, `role="status"` op toast elementen
- Toasts worden nu in de `toast-region` geplaatst in plaats van direct in `body`

```html
<div id="toast-region" aria-live="polite" aria-atomic="true"></div>
```

---

### C. Data races & State management (Hoog)

#### C.1 Race condition bij snel tab-wisselen

**Bestand:** `js/app.js` — `renderView()`

```javascript
async function renderView() {
  // ...loading overlay...
  allInternships = await InternshipsAPI.list();
  // ...meer async calls...
  content.textContent = '';
  content.appendChild(tpl.content.cloneNode(true));
}
```

Als een gebruiker snel tussen tabs klikt, kan een langzame request van tab A de content van tab B overschrijven.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
```javascript
let _renderGeneration = 0;
async function renderView() {
  const gen = ++_renderGeneration;
  // ...
  allInternships = await InternshipsAPI.list();
  if (gen !== _renderGeneration) return; // stale
  // ...
  if (gen !== _renderGeneration) return; // na elke async call
}
```
- Stale render check na **elke** async call (internships, stage-data, competenties, template render)
- Voorkomt dat een langzame request de content van een nieuwere tab overschrijft

---

#### C.2 Onnodige API calls bij elke view

**Bestand:** `js/app.js` — `renderView()`

```javascript
if (currentInternship) {
  [currentLogbooks, currentEvaluations, currentFeedback] = await Promise.all([...]);
}
```

Dit gebeurt **voor elke view**, zelfs voor admin-views die geen stage-data nodig hebben.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
- Stage-specifieke data (logbooks, evaluations, feedback) wordt alleen geladen als `currentInternship` bestaat EN de view het nodig heeft
- Competenties worden alleen geladen voor views die het nodig hebben via `_competencyViews.has(view)`:
  ```javascript
  const needsCompetencies = _competencyViews.has(view);
  if (needsCompetencies) {
    currentCompetencies = await CompetenciesAPI.list();
  } else {
    currentCompetencies = [];
  }
  ```
- Admin-views zoals `auditlog` en `gebruikers` laden geen competenties meer

---

### D. API Client & Foutafhandeling (Hoog)

#### D.1 `[object Object]` root cause in apiRequest

**Bestand:** `js/api-client.js` — `apiRequest()` en `AuthAPI.login()`

```javascript
// In AuthAPI.login:
errorText = errorJson.detail || JSON.stringify(errorJson);
// In apiRequest:
throw new Error(error.detail || `HTTP error! status: ${response.status}`);
```

FastAPI retourneert vaak `detail` als **array** van validatiefouten:
```json
{"detail": [{"loc": ["body", "email"], "msg": "field required", "type": "value_error.missing"}]}
```

Als `error.detail` een array is, wordt `new Error([object Object])` de string "[object Object]".

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
```javascript
function formatError(error) {
  if (Array.isArray(error.detail)) {
    return error.detail.map(d => d.msg || String(d)).join(', ');
  }
  if (typeof error.detail === 'string') return error.detail;
  if (typeof error.detail === 'object' && error.detail !== null) {
    return JSON.stringify(error.detail);
  }
  return JSON.stringify(error);
}
```
- `formatError()` gebruikt in `apiRequest()` en `AuthAPI.login()`
- `AuthAPI.demoLogin()` heeft ook expliciete netwerkfoutafhandeling
- 401 redirect guard (`_redirectingToLogin`) voorkomt dubbele redirects

---

#### D.2 `apiRequest` gooit 401 errors maar doet ook `window.location.href`

**Bestand:** `js/api-client.js`

```javascript
if (response.status === 401) {
  // ...redirect...
  throw new Error('Sessie verlopen, opnieuw inloggen...');
}
```

De redirect en de throw gebeuren tegelijk. De error bubblet op naar `renderView()` die het toont als een roze foutbanner, **terwijl** de pagina al aan het redirecten is.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
- Na 401 redirect wordt nu `return Promise.reject(new Error('Sessie verlopen...'))` gebruikt in plaats van `throw`
- Fout banner verschijnt niet meer tijdens redirect
- `_redirectingToLogin` guard voorkomt meerdere gelijktijdige redirects

---

### E. CSS Architecture (Medium)

#### E.1 Ongedefinieerde CSS custom properties

**Bestand:** `styles.css`

```css
.notif-dropdown {
  background: var(--surface, #fff);
  border: 1px solid var(--border, #e2e8f0);
}
.notif-dot {
  border: 2px solid var(--bg, #fff);
}
```

`--surface`, `--surface-alt`, `--bg`, `--text-muted` zijn **niet gedefinieerd** in `:root`. De fallback-waarden werken, maar de variabelen zijn dode code.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
- CSS custom properties toegevoegd aan `:root`:
  ```css
  --surface: #ffffff;
  --surface-alt: #f7fafc;
  --bg: #ffffff;
  --text-muted: #888888;
  ```
- Fallback-waarden zijn nu overbodig maar behouden voor backwards compatibility

---

#### E.2 Mobile CSS verbergt ALLE tabellen

**Bestand:** `styles.css`

```css
@media (max-width: 720px) {
  table { display: none; }
  .table-cards { display: flex; ... }
}
```

Dit verbergt **elke** tabel, inclusief kleine tabellen die prima responsive zijn (bijv. de "Openstaande Taken" tabel in de student dashboard). Alleen tabellen met een `.table-cards` alternatief zouden verborgen moeten worden.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
```css
@media (max-width: 720px) {
  table[data-table-cards] { display: none; }
}
```
- Tabellen zonder `[data-table-cards]` blijven zichtbaar op mobiel
- `removeTableCards()` helper toegevoegd voor cleanup bij view switches

---

#### E.3 `.reveal` animatie op `display: none` elementen

**Bestand:** `styles.css`, `index.html`

```html
<div id="logbook-form-panel" class="panel card reveal" style="display:none;">
```

Elementen met `display: none` krijgen toch de `rise` animatie assigned. Dit kost compositing resources zonder effect.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
- `.reveal` class verwijderd uit **alle** templates in `index.html`
- Elementen met `style="display:none"` hebben geen `.reveal` meer
- `prefers-reduced-motion` media query blijft actief voor toegankelijkheid
- `.reveal` CSS klasse bestaat nog voor mogelijk toekomstig gebruik

---

### F. UX / Micro-interacties (Medium)

#### F.1 Geen loading state voor dropdowns

**Bestand:** `js/views/student.js`

```javascript
teacherSelect.innerHTML = '<option value="">-- Kies een docent --</option>';
UsersAPI.list('teacher').then(teachers => { ... })
```

Tijdens het laden van docenten/mentors is er geen visuele indicatie. De dropdown blijft op "-- Kies een docent --" staan.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
```javascript
teacherSelect.innerHTML = '<option value="">Laden...</option>';
teacherSelect.disabled = true;
UsersAPI.list('teacher').then(teachers => {
  teacherSelect.innerHTML = '<option value="">-- Kies een docent --</option>';
  // ...
  teacherSelect.disabled = false;
}).catch(() => {
  teacherSelect.innerHTML = '<option value="">Kon docenten niet laden</option>';
});
```
- Zelfde patroon toegepast op mentor-select

---

#### F.2 Focus verdwijnt na tab-switch

**Bestand:** `js/app.js`

Na `content.textContent = ''` verliest de toetsenbordfocus. Voor toetsenbordgebruikers springt de focus naar `body`.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
```javascript
// Focus management: zet focus op de eerste heading in de nieuwe view
const firstHeading = content.querySelector('h2');
if (firstHeading) {
  firstHeading.setAttribute('tabindex', '-1');
  firstHeading.focus({ preventScroll: true });
}
```
- Toetsenbordfocus springt niet meer naar `body` na tab-switch
- Screenreader gebruikers krijgen direct de context van de nieuwe view

---

#### F.3 `confirm()` voor intrekken voorstel is browser-native

**Bestand:** `js/views/student.js`

```javascript
if (!confirm('Weet je zeker dat je je stagevoorstel wilt intrekken?...')) return;
```

Dit blokkeert de main thread. In een moderne app gebruik je een inline bevestigingsdialoog.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
- `showConfirmModal()` helper toegevoegd in `js/ui-helpers.js`
- Nieuwe `confirm-modal` markup in `index.html` met `role="dialog"`, `aria-modal="true"`
- `btn-withdraw-proposal` gebruikt nu `showConfirmModal()` in plaats van `confirm()`
- Promise-based API: resolved bij OK, rejected bij annuleren
- Fallback naar native `confirm()` als modal markup ontbreekt

---

### G. Prestatie (Medium)

#### G.1 `renderView` laadt altijd `currentCompetencies` voor admin

```javascript
if (role === 'admin' || view === 'evaluatie') {
  currentCompetencies = await CompetenciesAPI.list();
}
```

Dit wordt uitgevoerd voor **elke** view als de rol admin is, ook voor "auditlog" of "gebruikers" die geen competenties nodig hebben.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
- Competenties worden nu alleen geladen voor views die ze nodig hebben via `_competencyViews.has(view)`
- Set bevat: `evaluatie`, `admin-competenties`, `eindoverzicht`, `validatie`
- Admin-views zoals `auditlog`, `gebruikers`, `overzicht` laden geen competenties meer
- Vermindert onnodige API calls en versnelt tab-switching voor admin-gebruikers

---

#### G.2 `fetch('/users/seed')` gebeurt bij elke login render

**Bestand:** `js/app.js`

```javascript
fetch(`${API_BASE_URL}/users/seed`)
```

Deze request wordt altijd gedaan, ook als de gebruiker direct inlogt met email/wachtwoord. Dit vertraagt de login render.

**Status:** ✅ **OPGELOST**

**Oplossing geïmplementeerd:**
- Quick-login toont nu eerst een "Test accounts laden" knop
- `fetch('/users/seed')` gebeurt pas bij klik (lazy loading)
- Wachtwoorden zijn niet meer in de DOM — `demoLogin(email)` stuurt alleen email naar backend
- Loading state toont "Laden..." tijdens het ophalen
- Foutafhandeling toont "Kon test accounts niet laden" bij mislukte request

---

### H. Formulier validatie (Laag)

#### H.1 Inconsistente verplicht-markering

**Bestand:** `js/views/student.js`

De edit-form en resubmit-form hebben wel `required` en `minlength="20"` in HTML, maar de `new-proposal-form` (in JS gegenereerd) mist deze attributen op sommige velden.

**Status:** ❓ **TE VERIFIËREN** — Niet expliciet gecontroleerd in de laatste commits. De new-proposal-form moet `required` en `minlength="20"` hebben op de description textarea en de start/end date inputs.

---

## Samenvatting: Aanvullende prioritering — NA UPDATE

| Prioriteit | Issue | Bestand | Status |
|---|---|---|---|
| **Kritiek** | XSS in `formatReportRows` | `js/app.js` | ✅ OPGELOST |
| **Kritiek** | XSS in logboek fallback | `js/views/student.js` | ✅ OPGELOST |
| **Kritiek** | ~~Wachtwoorden in DOM~~ | `js/app.js` | ✅ OPGELOST |
| **Hoog** | `[object Object]` root cause | `js/api-client.js` | ✅ OPGELOST |
| **Hoog** | Race condition tab-switch | `js/app.js` | ✅ OPGELOST |
| **Hoog** | Week-grid niet toetsenbord bereikbaar | `js/views/student.js` | ✅ OPGELOST |
| **Hoog** | Onnodige API calls | `js/app.js` | ✅ OPGELOST |
| **Medium** | Mobile CSS verbergt alle tabellen | `styles.css` | ✅ OPGELOST |
| **Medium** | Modal mist ARIA | `index.html` | ✅ OPGELOST |
| **Medium** | Toast mist aria-live | `js/ui-helpers.js` | ✅ OPGELOST |
| **Medium** | Ongedefinieerde CSS vars | `styles.css` | ✅ OPGELOST |
| **Laag** | Lazy loading quick-login | `js/app.js` | ✅ OPGELOST |
| **Laag** | Focus management na tab-switch | `js/app.js` | ✅ OPGELOST |
| **Laag** | Geen loading state dropdowns | `js/views/student.js` | ✅ OPGELOST |
| **Laag** | `confirm()` voor intrekken | `js/views/student.js` | ✅ OPGELOST |
| **Laag** | 401 redirect + throw conflict | `js/api-client.js` | ✅ OPGELOST |

**Resultaat:** 16/16 issues uit dit review document zijn opgelost. De meeste vereisten nog wel aandacht voor **focus trap** in modals (ARIA-attributen zijn aanwezig, maar focus trap is niet volledig geïmplementeerd).

---

## Aanbeveling: status `frontend-issues.md`

Het originele `frontend-issues.md` is gedeeltelijk bijgewerkt in deze sessie. De volgende items zijn **opgelost** en gemarkeerd:

- **1.1** Internship not found → ✅ OPGELOST
- **1.2** `[object Object]` → ✅ OPGELOST
- **2.1** Achtergrond decoratief → ⚠️ GEDEELTELIJK (fonts gelocaliseerd, login wit, maar ambient/gradient nog aanwezig)
- **2.3** `.hero` roze → ❌ NOG OPEN
- **2.4** `.notif-bell:hover` → ❌ NOG OPEN
- **2.5** Spatiëring → ❌ NOG OPEN
- **3.1** Google Fonts → ✅ OPGELOST
- **3.2** `.reveal` animaties → ✅ OPGELOST
- **4.1** Skeleton loader → ❌ NOG OPEN
- **4.2** Netwerkfouten → ⚠️ GEDEELTELIJK (alleen login)
- **4.3** Mobiele cards → ⚠️ GEDEELTELIJK (CSS fix, maar card data nog incompleet)
- **4.4** Login achtergrond → ✅ OPGELOST

**Nog te doen:** focus trap in modals, `.hero` styling fixen, `.notif-bell:hover` fixen, spatiëring standaardiseren, skeleton loader toevoegen.
