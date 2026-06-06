# Product

## Register

product

## Users

Students, teachers, committee members, mentors, and administrators at Erasmus Hogeschool Brussel's Toegepaste Informatica program. Students track their internship progress, submit logbooks, and upload agreements. Teachers review logbooks and give feedback. Committee members approve or reject internship proposals and agreements. Mentors validate weekly logbooks. Administrators manage competencies, users, and system-wide oversight.

Context: Most users visit briefly to complete a specific task. Students check status between classes. Teachers review during office hours. Admins manage in batches. No one browses this for fun.

## Product Purpose

Replace the scattered spreadsheet-and-email workflow for internship tracking with a single source of truth. Every stakeholder sees the same data, in the role-appropriate view, without asking "where is that file?" Success: zero emails asking for status updates, every logbook submitted on time, every agreement processed without friction.

## Brand Personality

Neutral and invisible. The tool should disappear so users focus on their internship, not the interface. Calm, efficient, competent. Like a well-organized filing cabinet: you never admire the cabinet, you just find what you need.

## Anti-references

- Enterprise SaaS dashboards (Jira, Linear, Asana): gray sidebars, metric cards, "seamless workflow" copy. This is not a productivity tool for teams; it is an academic tracking system.
- Consumer playful apps (Duolingo-style gamification, bright gradients). This is academic software, not entertainment.
- Bureaucratic portals (government forms, legacy university systems). Dense, form-heavy, hostile to scanning.
- AI-generated cream/sand/paper backgrounds. The warm-neutral monoculture is a tell.

## Design Principles

1. **One job per screen.** Every view has a single purpose. If a user has to think about what to do next, the design failed.
2. **Information density without clutter.** Show what matters, hide what doesn't. Scannable, not sparse. Every pixel earns its place.
3. **Role-aware, never role-confused.** Each user type sees exactly what they need and nothing they don't. No "admin features leaking into student views."
4. **Progress is visible.** Students always know where they stand: what's done, what's pending, what's overdue. Status should be glanceable, not buried.
5. **The tool disappears.** No decorative elements that don't serve a function. No illustrations for illustration's sake. Content and structure carry the visual weight.

## Accessibility & Inclusion

WCAG AA minimum. Proper contrast ratios, keyboard navigation, ARIA labels on interactive elements, semantic HTML structure. Reduced motion support via `prefers-reduced-motion`. The app is already Dutch-language; maintain that. Consider screen reader compatibility for the role-based navigation.
