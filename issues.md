# Issues - Stage Monitoring Tool

Review of https://stage-monitoring-demo.fly.dev/

## Security

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| S1 | **High** | JWT token stored in `localStorage` — vulnerable to XSS theft. Should use httpOnly cookies instead. | `js/api-client.js:10-30` |
| S2 | **High** | Demo endpoint `GET /api/users/seed` exposes all test accounts. Must not exist in production. | Login quick-login feature |
| S3 | **Medium** | No Content Security Policy (CSP) headers set — no protection against inline script injection. | Server config |
| S4 | **Medium** | No rate limiting on login endpoint — brute force possible. | Backend `/api/auth/login` |
| S5 | **Medium** | Password field has no minimum length validation on the frontend. | `index.html` login template |
| S6 | **Low** | `innerHTML` used in `showToast()` — safe because of `escapeHtml()`, but risky pattern if escape is ever bypassed. | `js/ui-helpers.js:163` |

## Accessibility

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| A1 | **High** | All `<table>` elements lack `<caption>` — screen readers can't identify table purpose. | All templates with tables |
| A2 | **Medium** | Status indicators rely on color only — logbook legend dots (`dot` class) have no text alternative. | `index.html` logbook template |
| A3 | **Medium** | Notification red dot has no `aria-label` or `aria-hidden` — screen readers announce it ambiguously. | `index.html` notif-dot |
| A4 | **Medium** | `aria-invalid` set on form fields but `aria-describedby` not consistently linked to error messages. | Login form |
| A5 | **Low** | Tab state changes not announced — `aria-selected` updates but no `aria-live` region for tab changes. | Navigation tabs |

## UI/UX

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| U1 | **Medium** | Login redirects with `window.location.href = 'index.html'` — full page reload loses SPA state. | `js/app.js:137` |
| U2 | **Medium** | No loading timeout — if API is down, spinner shows indefinitely with no user recourse. | `js/app.js:283-292` |
| U3 | **Medium** | Quick login section loads async, causing layout shift on login page. | Login page |
| U4 | **Medium** | Mixed language status values — API returns English (`approved`) and Dutch (`goedgekeurd`) causing mismatched status pills. | API responses + `getStatusClass()` |
| U5 | **Low** | No offline handling or retry UX when network errors occur. | `js/api-client.js` fetch catch |
| U6 | **Low** | `loadAllInternships()` fetches ALL records into memory — could be problematic with thousands of internships. | `js/app.js:205-213` |

## Architecture

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| AR1 | **Medium** | All state is module-level globals (`allInternships`, `currentLogbooks`, etc.) — fragile and hard to test. | `js/app.js:14-21` |
| AR2 | **Medium** | `_renderGeneration` race condition pattern — could use `AbortController` for cleaner cancellation. | `js/app.js:195` |
| AR3 | **Low** | All `<template>` elements loaded upfront regardless of user role — admin templates sent to students. | `index.html` |
| AR4 | **Low** | No code splitting or lazy JS loading — all scripts loaded on every page. | `index.html` script tags |
| AR5 | **Low** | Cache-busting uses `?v=2026-06-06-1` hardcoded date — won't bust within same day. | `index.html` script/link tags |
| AR6 | **Low** | Cache TTL of 30s for competencies causes unnecessary re-fetches on fast view switching. | `js/api-client.js:225` |

## Performance

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| P1 | **Medium** | Notification polling continues when browser tab is hidden — wastes battery/data. | `js/notifications.js:54` |
| P2 | **Low** | No preload hints for favicon/logo SVGs. | `index.html` head |

## Code Quality

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| C1 | **Medium** | Mixed Dutch/English in codebase — variable names are English, UI is Dutch, API responses mix both. | Throughout |
| C2 | **Low** | No TypeScript or JSDoc — no type safety, harder to refactor safely. | All JS files |
| C3 | **Low** | Magic numbers throughout: `30_000`, `200`, `50`, `3000`. Should be named constants. | `js/app.js`, `js/api-client.js` |
| C4 | **Low** | Some functions are very long and could be broken down (`renderStudentDashboard`, `renderCommitteeProposals`). | `js/views/*.js` |

## Design

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| D1 | **Medium** | Login page loses the app gradient background (`body.login-active { background: #ffffff }`) — feels like a different application. | `styles.css` login-active |
| D2 | **Medium** | Dashboard hero card ("Mijn Stage") has same visual weight as other cards — should stand out as the primary information hub. | `index.html` student-dashboard-template |
| D3 | **Medium** | Tables are visually dense — tight row padding makes scanning difficult, especially on longer lists. | `styles.css` table styles |
| D4 | **Medium** | Two-column grid persists too long on tablets (720-980px) — content gets cramped before the single-column breakpoint. | `styles.css` two-col grid |
| D5 | **Low** | Inline styles (`margin-top: 1rem`, `display: none`) scattered throughout templates — inconsistent spacing and hard to maintain. | All templates |
| D6 | **Low** | Admin weight chart is a plain bar — a donut or pie chart would communicate weight distribution more effectively. | Admin template, weight-chart |
| D7 | **Low** | No empty state illustrations — empty views (no logbooks, no evaluations) show plain text, making the app feel broken. | All empty states |

## Usability

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| UB1 | **High** | Logbook day-grid cells are `min-width: 32px` — below the 44px WCAG touch target minimum. Users will misclick on mobile. | `js/views/student.js` day-cell |
| UB2 | **Medium** | No breadcrumb or wayfinding — when deep in a form (editing proposal), users lose context of where they are. | All views |
| UB3 | **Medium** | Committee proposal review appears below the table — requires scrolling back and forth on long lists. A modal or side panel would be better. | `index.html` commissie-template |
| UB4 | **Medium** | Internship selector dropdown blends in with tab styling — for teachers/mentors managing multiple internships, this critical control should be more prominent. | `styles.css` nav-stage-selector |
| UB5 | **Medium** | "Nieuw stagevoorstel" button appears on existing approved proposals — unclear if this creates a new internship or replaces the current one. | `js/views/student.js` wireProposalForm |
| UB6 | **Medium** | Quick login requires clicking "Test accounts laden" first — on a demo site, accounts should load by default to reduce friction. | `js/app.js` renderLogin |
| UB7 | **Low** | No undo/toast-with-undo for destructive actions (submit logbook, withdraw proposal) — immediate and irreversible. | All action handlers |
| UB8 | **Low** | No global search — users can't search across internships, students, or logbooks from a single place. | App-wide |
| UB9 | **Low** | Evaluation flow relationship (self-eval → teacher eval → mentor eval) is not explained to students. | Student evaluations view |
| UB10 | **Low** | "Overeenkomsten" label appears in 3 roles with different contexts — could confuse users when switching roles in demo. | Committee, admin, student views |

## Mobile

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| M1 | **High** | Logbook day-grid cells too small for touch — `min-width: 32px` with 7 cells per row. | `js/views/student.js` day-cell |
| M2 | **Medium** | Nav tabs stack vertically on mobile but 5+ tabs make the nav very long — could use horizontal scroll or hamburger menu. | `styles.css` @media 720px |
| M3 | **Medium** | Notification dropdown is `width: 320px` — overflows on 375px screens. | `styles.css` notif-dropdown |
| M4 | **Low** | Horizontal-scrolling tables (`min-width: 640px`) lack a visible scroll affordance — users may not realize there's more content. | `styles.css` @media 720px |

## Design Principles

### Color

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| DP1 | **Medium** | `--ink-soft` (#425466) contrast ratio ~5.2:1 on white — fails WCAG AAA, borderline at small sizes (0.82rem hints). | `styles.css:6` |
| DP2 | **Medium** | `--accent` (#c73d50) contrast ratio ~4.1:1 on white — borderline for small text. Buttons OK (white on coral = 7:1+). | `styles.css:7` |
| DP3 | **Low** | `--info-text` (#005564) and `--accent-2` (#00798c) are both teal — unclear distinction between "info text" and "accent color". | `styles.css:8,22` |
| DP4 | **Low** | No dark mode support — entire palette is light-mode only. | `:root` |

### White Space & Spacing

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| DP5 | **Medium** | No formal spacing scale — values are ad-hoc (`0.33rem`, `0.58rem`, `0.72rem`, `0.88rem`). Should use 4px/8px base. | Throughout |
| DP6 | **Medium** | Table cell padding is tight (`0.5rem`) — rows feel cramped, especially on longer lists. | `styles.css:497-501` |
| DP7 | **Low** | Label margin inconsistent — global rule vs inline styles in templates (`0.35rem` vs `0.75rem`). | `styles.css:118-124` |
| DP8 | **Low** | Hero card has no extra spacing — identical `padding: 1rem` to other cards. Should be more prominent. | `styles.css:178,288-291` |

### Typography

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| DP9 | **Medium** | No explicit type scale — sizes are ad-hoc (`0.82rem`, `0.85rem`, `0.86rem`, `0.9rem`, `0.95rem`, `1rem`, `1.1rem`, `1.5rem`). Should use a modular scale. | Throughout |
| DP10 | **Medium** | Labels at 0.86rem (~13.8px) and hints at 0.82rem (~13.1px) are below recommended 14px minimum for body text. | `styles.css:118-129` |
| DP11 | **Low** | No `line-height` standardization — body defaults to browser (~1.5), toast uses 1.4, no consistent vertical rhythm. | Throughout |
| DP12 | **Low** | Heading hierarchy unclear — `h1`, `h2`, `h3` share one CSS rule with no size distinction defined. | `styles.css:110-114` |

### Border Radius

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| DP13 | **Low** | No radius token — values hardcoded as `6px`, `8px`, `10px`, `12px`. Should define `--radius-sm/md/lg`. | Throughout |
| DP14 | **Low** | 10px (nav tabs) vs 8px (buttons) distinction is nearly indistinguishable. Could unify. | `styles.css:207,338` |

### Shadows & Depth

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| DP15 | **Medium** | Cards have no shadow by default — rely on `border` only. Adding subtle shadow would enhance depth. | `styles.css:170-176` |
| DP16 | **Low** | `--shadow` token defined but only used on modals — underutilized. | `styles.css:13` |
| DP17 | **Low** | No elevation system — no distinction between surface levels (base, raised, floating). | — |

### Motion & Transitions

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| DP18 | **Low** | No transition token system — each element defines its own timing. Should define `--ease-out`, `--duration-fast/normal`. | Throughout |
| DP19 | **Low** | Nav tab hover is aggressive — `translateY(-3px)` + shadow on every hover could feel jarring in a professional tool. | `styles.css:219-224` |
| DP20 | **Low** | No micro-interactions on status changes — status pill text changes without transition. | — |

## Priority Fixes for Production

1. **Move JWT to httpOnly cookies** (S1)
2. **Add `<caption>` to all tables** (A1)
3. **Add loading timeout/fallback** (U2)
4. **Remove `/api/users/seed` endpoint** (S2)
5. **Add CSP headers** (S3)
6. **Fix status value language consistency** (U4)
7. **Pause notification polling when tab hidden** (P1)
8. **Increase logbook day-grid cell size to 44px minimum** (UB1, M1)
9. **Add visual hierarchy to dashboard hero card** (D2)
10. **Use modal/slide-out for committee proposal review** (UB3)

## Summary

| Category | Issues | Avg Severity |
|----------|--------|--------------|
| Security | 6 | Medium-High |
| Accessibility | 5 | Medium |
| UI/UX | 6 | Medium |
| Architecture | 6 | Medium |
| Performance | 2 | Low-Medium |
| Code Quality | 4 | Low |
| Design | 7 | Low-Medium |
| Usability | 10 | Medium |
| Mobile | 4 | Medium |
| Design Principles | 20 | Low-Medium |
| **Total** | **70** | |
