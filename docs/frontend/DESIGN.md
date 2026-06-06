---
name: Stage Monitoring Tool
description: Internship tracking system for Erasmus Hogeschool Brussel
colors:
  ink: "#12263a"
  ink-soft: "#425466"
  accent: "#c73d50"
  accent-deep: "#b83d4e"
  teal: "#00798c"
  teal-deep: "#006878"
  good: "#3c9d78"
  good-deep: "#328a67"
  warn: "#e09f3e"
  bad: "#d62839"
  bad-deep: "#b8222f"
  bg-warm: "#f4f0e6"
  bg-cool: "#d9e6f2"
  surface: "#ffffff"
  border: "rgba(18, 38, 58, 0.12)"
  good-bg: "rgba(60, 157, 120, 0.15)"
  warn-bg: "rgba(224, 159, 62, 0.15)"
  bad-bg: "rgba(214, 40, 57, 0.15)"
  info-bg: "rgba(0, 121, 140, 0.15)"
typography:
  display:
    fontFamily: "Space Grotesk, sans-serif"
    fontWeight: 700
  body:
    fontFamily: "IBM Plex Sans, sans-serif"
    fontWeight: 400
    fontSize: "1rem"
    lineHeight: 1.5
  label:
    fontFamily: "IBM Plex Sans, sans-serif"
    fontWeight: 600
    fontSize: "0.86rem"
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
  xl: "12px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "0.75rem"
  lg: "1rem"
  xl: "1.5rem"
  xxl: "2rem"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "0.58rem 0.88rem"
  button-primary-hover:
    backgroundColor: "{colors.accent-deep}"
    textColor: "#ffffff"
  button-secondary:
    backgroundColor: "{colors.teal}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "0.58rem 0.88rem"
  button-secondary-hover:
    backgroundColor: "{colors.teal-deep}"
  button-success:
    backgroundColor: "{colors.good}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
  button-danger:
    backgroundColor: "{colors.bad}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.md}"
    padding: "0.58rem 0.88rem"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0.6rem 0.7rem"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.xl}"
    padding: "1rem"
  nav-tab:
    backgroundColor: "rgba(255,255,255,0.28)"
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.lg}"
    padding: "0.72rem 1.3rem"
  nav-tab-active:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
  status-pill:
    rounded: "{rounded.sm}"
    padding: "0.25rem 0.6rem"
---

# Design System: Stage Monitoring Tool

## 1. Overview

**Creative North Star: "The Well-Organized Office"**

Every element earns its place. The interface is a quiet workspace: surfaces are clean, navigation is direct, and data is always scannable. Like a well-organized filing cabinet, you never admire the cabinet; you find what you need and move on.

The system rejects the enterprise SaaS dashboard (gray sidebars, metric cards, "seamless workflow" copy), the playful consumer app (gamification, bright gradients), and the bureaucratic portal (dense forms, hostile scanning). No cream/sand/paper warm-neutral monoculture. No decorative illustrations. No gradient text. Content and structure carry the visual weight; the tool disappears.

**Key Characteristics:**
- Flat surfaces with tonal layering for depth, no ambient shadows at rest
- Two-font hierarchy: Space Grotesk for headings, IBM Plex Sans for everything else
- Crimson accent for primary actions, teal for secondary; both used sparingly
- Border-based separation over shadow-based elevation
- Status communicated through tinted background pills, not colored borders or icons alone
- Single-column forms, scannable tables, role-aware navigation

## 2. Colors

A restrained palette anchored by two functional accents (crimson for primary, teal for secondary) against warm and cool tinted neutrals. The palette is institutional without being cold.

### Primary
- **Crimson Accent** (#c73d50): Primary action buttons, active nav tabs, focus rings, status accents. Used on ≤15% of any screen; its rarity is the point.
- **Crimson Deep** (#b83d4e): Hover state for primary actions.

### Secondary
- **Teal** (#00798c): Secondary buttons, focus outlines, informational accents, link hover states.
- **Teal Deep** (#006878): Hover state for secondary actions.

### Tertiary
- **Good Green** (#3c9d78): Success states, completed status, positive indicators.
- **Warn Amber** (#e09f3e): Warning states, draft status, pending attention.
- **Bad Red** (#d62839): Error states, rejected status, destructive actions.

### Neutral
- **Ink** (#12263a): Primary body text, headings, high-contrast foreground. Dark navy, not pure black.
- **Ink Soft** (#425466): Secondary text, labels, hints, muted content. Readable against white and warm backgrounds.
- **Surface** (#ffffff): Card backgrounds, input backgrounds, modal backgrounds.
- **Border** (rgba(18, 38, 58, 0.12)): Subtle dividers, card borders, table separators. Never stronger than 0.15 opacity.
- **Bg Warm** (#f4f0e6): Primary page background. Warm off-white with slight yellow undertone.
- **Bg Cool** (#d9e6f2): Secondary background accent, used in radial gradients for visual interest.

### Named Rules
**The Accent Rarity Rule.** The crimson accent appears on primary actions and active states only. It is never used for decorative purposes, background tints, or large surface areas. Its visual weight comes from restraint.

**The Tinted-Neutral Rule.** Status backgrounds (good-bg, warn-bg, bad-bg, info-bg) use the status color at 15% opacity. Text on these backgrounds uses a darker shade of the same hue, not the base ink color. This ensures status is communicated by both background and text hue.

## 3. Typography

**Display Font:** Space Grotesk (with system sans-serif fallback)
**Body Font:** IBM Plex Sans (with system sans-serif fallback)

**Character:** Space Grotesk carries the headings with geometric confidence. IBM Plex Sans handles body text with humanist warmth and excellent readability at small sizes. The pairing is functional, not decorative.

### Hierarchy
- **Display** (700, clamp(2rem, 4vw, 2.5rem), 1.1): Page titles in the topbar. Only appears once per view.
- **Headline** (700, 1.5rem, 1.2): Section headings within panels ("Mijn Stage", "Logboeken Overzicht").
- **Title** (700, 1.25rem, 1.3): Subsection headings, modal titles.
- **Body** (400, 1rem, 1.5): Primary content text, descriptions, paragraphs. Max line length 65-75ch.
- **Label** (600, 0.86rem, normal): Form labels, field descriptions, hints. Not uppercase.

### Named Rules
**The No-Uppercase Rule.** Body copy is never uppercase. Labels and section eyebrows may use uppercase sparingly (≤4 words), but the default is sentence case. Uppercase at body sizes is unreadable.

**The Weight-Contrast Rule.** Hierarchy is established through weight contrast (≥1.25 ratio between steps), not size alone. Headings are 700, body is 400, labels are 600. This three-weight system is sufficient.

## 4. Elevation

Flat with tonal layering. Surfaces are flat at rest. Depth is conveyed through background tinting (warm cream bg, white cards, subtle border lines), not shadows. The single shadow variable (`--shadow: 0 20px 45px rgba(18, 38, 58, 0.12)`) appears only on elevated elements like modals and toast notifications, not on cards or standard containers.

### Shadow Vocabulary
- **Elevated** (`box-shadow: 0 20px 45px rgba(18, 38, 58, 0.12)`): Modals, toast notifications. Elements that float above the main content layer.
- **Hover lift** (`box-shadow: 0 8px 22px rgba(18,38,58,0.08)`): Nav tabs on hover, week cells on hover. Temporary elevation that responds to interaction.

### Named Rules
**The Flat-By-Default Rule.** Cards, panels, and containers have no shadow at rest. Shadows appear only as a response to state (hover, active modal) or as a result of floating position (toast, dropdown). If a card has a shadow without user interaction, the shadow is wrong.

**The Border-First Rule.** Separation between elements is achieved through 1px borders at `rgba(18, 38, 58, 0.12)`, not shadows or background changes. Shadows supplement borders on floating elements only.

## 5. Components

### Buttons
- **Shape:** Gently curved (8px radius). Full-pill for small tags/badges only.
- **Primary:** Crimson background (#c73d50), white text, 0.58rem 0.88rem padding. Translates up 1px on hover with deepened crimson.
- **Secondary:** Teal background (#00798c), white text. Same hover pattern.
- **Success / Danger:** Green or red background, white text. Used for confirm/delete actions.
- **Ghost / Logout:** Transparent background, ink-soft text, 1px border. Hover fills with rgba(18, 38, 58, 0.06).
- **Focus:** 2px solid teal outline with 2px offset. Never the crimson accent for focus.
- **Disabled:** 0.6 opacity, not-allowed cursor, no transform on hover.

### Cards / Containers
- **Corner Style:** 12px radius (xl).
- **Background:** White (#ffffff).
- **Shadow Strategy:** None at rest. Flat-by-default rule applies.
- **Border:** 1px solid rgba(18, 38, 58, 0.12). Always present, never stronger.
- **Internal Padding:** 1rem (card), 0.85rem (table cards on mobile).

### Inputs / Fields
- **Style:** 1px border at rgba(18, 38, 58, 0.12), white background, 8px radius. Padding 0.6rem 0.7rem.
- **Focus:** Border shifts to teal (#00798c), 3px box-shadow ring at rgba(0, 121, 140, 0.1). No outline.
- **Error:** Border shifts to bad red (#d62839). No additional error icon or message unless contextual.
- **Placeholder:** Ink-soft at 0.6 opacity. Must maintain 4.5:1 contrast.

### Navigation Tabs
- **Style:** Horizontal tab bar below the topbar. Flexbox wrap, gap-based spacing.
- **Default:** Transparent background, ink-soft text, 1px border, 10px radius.
- **Hover:** Subtle rgba(18, 38, 58, 0.10) fill, translates up 3px with ambient shadow.
- **Active:** Crimson background, white text, font-weight 700.
- **Mobile:** Full-width stacked tabs.

### Status Pills
- **Style:** Inline-block, 6px radius, 0.25rem 0.6rem padding, 0.85rem font, font-weight 600.
- **Info:** Teal-tinted background, dark teal text.
- **Warning:** Amber-tinted background, dark amber text.
- **Success:** Green-tinted background, dark green text.
- **Error:** Red-tinted background, dark red text.

### Tables
- **Style:** Full-width, border-collapse. 1px bottom border per row at rgba(18, 38, 58, 0.12).
- **Header:** 0.85rem, font-weight 600, ink-soft color. No background.
- **Rows:** Cursor pointer on interactive rows (proposals), subtle teal-tinted hover.
- **Mobile:** Tables hide; replaced by card-based layout (table-cards).

### Week Grid (Logbooks)
- **Style:** CSS Grid, auto-fill, minmax(60px, 1fr). Each cell is a clickable card.
- **States:** Submitted (green-tinted bg), Draft (amber-tinted bg), Missing (white, muted text).
- **Hover:** Translates up 2px with subtle shadow.
- **Selected:** 3px solid teal outline with 2px offset.

### Modal
- **Style:** Fixed overlay with backdrop blur (4px). Card centered, max-width 480px, 12px radius.
- **Animation:** Rise-in (translateY + opacity) over 200ms ease.
- **Shadow:** Elevated shadow (0 20px 45px rgba(18, 38, 58, 0.12)).

### Toast Notifications
- **Style:** Fixed top-right, white background, 12px radius, 1px border. Slides in from right.
- **States:** Border color shifts per type (green/amber/red/teal).
- **Icon:** 28px circle with tinted background and colored icon.

## 6. Do's and Don'ts

### Do:
- **Do** use 1px borders at rgba(18, 38, 58, 0.12) for all separation between elements. This is the primary visual divider.
- **Do** use tinted status backgrounds (15% opacity of the status color) with darker-shade text for status communication.
- **Do** keep the crimson accent on primary actions only. Its rarity is the point.
- **Do** use Space Grotesk for headings and IBM Plex Sans for body. Never mix in a third font family.
- **Do** hide tables on mobile and render card-based alternatives. The viewport is part of the design.
- **Do** support `prefers-reduced-motion: reduce` with instant transitions or crossfades. Every animation needs this alternative.
- **Do** use `text-wrap: balance` on h1-h3 for even line lengths.
- **Do** ensure placeholder text maintains 4.5:1 contrast against its background. The ink-soft color at 0.6 opacity is the minimum.

### Don't:
- **Don't** use `border-left` or `border-right` greater than 1px as a colored accent on cards, list items, or alerts. Never intentional. Rewrite with full borders, background tints, or nothing.
- **Don't** use `background-clip: text` with gradients. Decorative, never meaningful. Use a single solid color.
- **Don't** use glassmorphism, blurs, or frosted-glass cards decoratively. The backdrop blur is reserved for modal overlays only.
- **Don't** use the hero-metric template (big number, small label, supporting stats, gradient accent). This is a SaaS cliché.
- **Don't** repeat identical card grids (same-sized cards with icon + heading + text). Cards earn their place individually.
- **Don't** put tiny uppercase tracked eyebrows above every section. One kicker as a deliberate brand system is voice; eyebrows everywhere is AI grammar.
- **Don't** use numbered section markers (01 / 02 / 03) as default scaffolding. Numbers earn their place when order carries information.
- **Don't** pair `border: 1px solid X` with `box-shadow: 0 Npx Mpx ...` where M ≥ 16px on the same element. Pick one.
- **Don't** use border-radius ≥ 24px on cards. Cards top out at 12px.
- **Don't** use cream/sand/paper/bone/linen/parchment as token names or body background strategies. The warm-neutral monoculture is a tell.
- **Don't** use marketing buzzwords (seamless, empower, supercharge, leverage, transform). Use specific nouns and verbs.
- **Don't** write em dashes. Use commas, colons, semicolons, or parentheses.
- **Don't** animate CSS layout properties unless truly needed. Use transform and opacity.
- **Don't** use bounce, elastic, or spring easing. Ease out with exponential curves.
