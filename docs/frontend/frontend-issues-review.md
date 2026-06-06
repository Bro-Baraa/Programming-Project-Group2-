# Aanvullend Review: Frontend Issues

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

**Oplossing:** `escapeHtml(name)` en `escapeHtml(r.student_description)` toepassen.

---

#### A.2 XSS in student logboek fallback

**Bestand:** `js/views/student.js` — `renderStudentDashboard()`

```javascript
// PROBLEEM: week_number, status, mentor_feedback niet geescaped
<td>${w.week_number}</td>
<td>${w.mentor_feedback ? w.mentor_feedback : '<span class="hint">-</span>'}</td>
```

**Oplossing:** `escapeHtml()` toepassen op alle dynamische strings.

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
cell.setAttribute('role', 'button');
cell.setAttribute('tabindex', '0');
cell.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') openWeek(w);
});
```

---

#### B.2 Notificatie dropdown mist `aria-expanded` en focus trap

**Bestand:** `js/notifications.js` (vermoedelijk), `index.html`, `styles.css`

- De bell-knop heeft geen `aria-expanded` state
- De dropdown verschijnt zonder focus management
- De dropdown sluit niet met `Escape` toets

**Oplossing:**
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

**Oplossing:**
```html
<div id="profile-modal" class="modal" role="dialog" aria-modal="true" aria-labelledby="profile-modal-title" style="display: none;">
  <h3 id="profile-modal-title">Profielen Beheren</h3>
```

---

#### B.4 Formulier validatie niet gekoppeld aan screenreaders

**Bestand:** `index.html` en `js/views/student.js`

Input velden met validatie-fouten hebben geen `aria-describedby` verwijzing naar de foutmelding.

**Oplossing:**
```html
<input id="login-email" aria-describedby="login-error" aria-invalid="true">
<p id="login-error" role="alert">...</p>
```

---

#### B.5 Toast notifications zonder `aria-live`

**Bestand:** `js/ui-helpers.js` (vermoedelijk)

Toasts verschijnen via CSS transform maar hebben geen `aria-live="polite"` container. Screenreader gebruikers missen ze.

**Oplossing:**
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

**Oplossing:**
```javascript
let renderGeneration = 0;
async function renderView() {
  const gen = ++renderGeneration;
  // ...
  allInternships = await InternshipsAPI.list();
  if (gen !== renderGeneration) return; // stale
}
```

---

#### C.2 Onnodige API calls bij elke view

**Bestand:** `js/app.js` — `renderView()`

```javascript
if (currentInternship) {
  [currentLogbooks, currentEvaluations, currentFeedback] = await Promise.all([...]);
}
```

Dit gebeurt **voor elke view**, zelfs voor admin-views die geen stage-data nodig hebben.

**Oplossing:** Laad stage-specifieke data alleen als de view het nodig heeft (bijv. `student-dashboard`, `logboek`, etc.), niet voor `admin-competenties`.

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

**Oplossing:**
```javascript
function formatError(error) {
  if (Array.isArray(error.detail)) {
    return error.detail.map(d => d.msg).join(', ');
  }
  if (typeof error.detail === 'string') return error.detail;
  return JSON.stringify(error);
}
```

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

**Oplossing:** Geen `throw` na een redirect. Return een rejected promise of gebruik een zachte redirect.

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

**Oplossing:** Voeg toe aan `:root` of verwijder de variabele-referenties.

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

**Oplossing:**
```css
@media (max-width: 720px) {
  table[data-table-cards] { display: none; }
}
```

---

#### E.3 `.reveal` animatie op `display: none` elementen

**Bestand:** `styles.css`, `index.html`

```html
<div id="logbook-form-panel" class="panel card reveal" style="display:none;">
```

Elementen met `display: none` krijgen toch de `rise` animatie assigned. Dit kost compositing resources zonder effect.

**Oplossing:** Verwijder `reveal` van initieel verborgen elementen, of voeg `.reveal` pas dynamisch toe bij het tonen.

---

### F. UX / Micro-interacties (Medium)

#### F.1 Geen loading state voor dropdowns

**Bestand:** `js/views/student.js`

```javascript
teacherSelect.innerHTML = '<option value="">-- Kies een docent --</option>';
UsersAPI.list('teacher').then(teachers => { ... })
```

Tijdens het laden van docenten/mentors is er geen visuele indicatie. De dropdown blijft op "-- Kies een docent --" staan.

**Oplossing:** `teacherSelect.disabled = true;` + "Laden..." optie tijdens de request.

---

#### F.2 Focus verdwijnt na tab-switch

**Bestand:** `js/app.js`

Na `content.textContent = ''` verliest de toetsenbordfocus. Voor toetsenbordgebruikers springt de focus naar `body`.

**Oplossing:** Sla de focus op voor de switch, en na renderen focus op een logisch element (bijv. het eerste `h2` in de nieuwe view via `tabindex="-1"`).

---

#### F.3 `confirm()` voor intrekken voorstel is browser-native

**Bestand:** `js/views/student.js`

```javascript
if (!confirm('Weet je zeker dat je je stagevoorstel wilt intrekken?...')) return;
```

Dit blokkeert de main thread. In een moderne app gebruik je een inline bevestigingsdialoog.

**Oplossing:** Vervang door een eigen modal met "Annuleren / Bevestigen".

---

### G. Prestatie (Medium)

#### G.1 `renderView` laadt altijd `currentCompetencies` voor admin

```javascript
if (role === 'admin' || view === 'evaluatie') {
  currentCompetencies = await CompetenciesAPI.list();
}
```

Dit wordt uitgevoerd voor **elke** view als de rol admin is, ook voor "auditlog" of "gebruikers" die geen competenties nodig hebben.

**Oplossing:** Verplaats naar de specifieke view handler (`renderCompetencyManager`).

---

#### G.2 `fetch('/users/seed')` gebeurt bij elke login render

**Bestand:** `js/app.js`

```javascript
fetch(`${API_BASE_URL}/users/seed`)
```

Deze request wordt altijd gedaan, ook als de gebruiker direct inlogt met email/wachtwoord. Dit vertraagt de login render.

**Oplossing:** Laad de quick-login dropdown pas als de gebruiker erop klikt (lazy loading).

---

### H. Formulier validatie (Laag)

#### H.1 Inconsistente verplicht-markering

**Bestand:** `js/views/student.js`

De edit-form en resubmit-form hebben wel `required` en `minlength="20"` in HTML, maar de `new-proposal-form` (in JS gegenereerd) mist deze attributen op sommige velden.

---

## Samenvatting: Aanvullende prioritering

| Prioriteit | Issue | Bestand |
|---|---|---|
| **Kritiek** | XSS in `formatReportRows` | `js/app.js` |
| **Kritiek** | XSS in logboek fallback | `js/views/student.js` |
| **Kritiek** | ~~Wachtwoorden in DOM~~ ✅ | `js/app.js` |
| **Hoog** | `[object Object]` root cause | `js/api-client.js` |
| **Hoog** | Race condition tab-switch | `js/app.js` |
| **Hoog** | Week-grid niet toetsenbord bereikbaar | `js/views/student.js` |
| **Hoog** | Onnodige API calls | `js/app.js` |
| **Medium** | Mobile CSS verbergt alle tabellen | `styles.css` |
| **Medium** | Modal mist ARIA | `index.html` |
| **Medium** | Toast mist aria-live | `js/ui-helpers.js` |
| **Medium** | Ongedefinieerde CSS vars | `styles.css` |
| **Laag** | Lazy loading quick-login | `js/app.js` |
| **Laag** | Focus management na tab-switch | `js/app.js` |

## Aanbeveling: aanpassen bestaand document

1. **Sectie 1 (Kritieke bugs):** Voeg XSS (A.1, A.2) en wachtwoorden in DOM (A.3) toe.
2. **Sectie 2 (Design):** Voeg E.2 (mobile CSS) toe.
3. **Nieuwe sectie 2.5 (Toegankelijkheid):** Voeg B.1 t/m B.5 toe.
4. **Sectie 3 (Prestatie):** Voeg C.2, G.1, G.2 toe.
5. **Nieuwe sectie 5 (Security):** Voeg A.1 t/m A.3 toe.
6. **Verduidelijk 1.2:** Het `[object Object]` probleem zit dieper dan alleen parsing — het zit in `apiRequest` en `AuthAPI.login` die geen array-details afhandelen.
