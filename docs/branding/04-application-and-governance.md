# 04 — Application & Governance

**Last Updated:** 2026-05-30

How the brand gets applied in code, the rules that protect it, and the
decisions still open.

---

## Token Migration: blue-500 → Brand Indigo

The interactive primary changes from `blue-500` (`#3b82f6`) to **Brand Indigo**
(`#4338ca`). Do this as **one design-token change**, not scattered edits.

**Plan**
1. Define a single source token (e.g. `--color-primary` / Tailwind theme
   `primary`) = Brand Indigo; `primary-hover` = `indigo-800`.
2. Point shadcn/ui theme variables at the token.
3. Grep for hardcoded `blue-500` / `blue-600` / `#3b82f6` / `#2563eb` and
   replace with the token.
4. Update `docs/design-guidelines.md` "Interactive Colors" table.
5. Visual QA: buttons, links, focus rings, active nav, selected rows.

**Audit targets:** Tailwind config, shadcn theme, `design-guidelines.md`,
component files using `blue-*` utilities.

---

## Accessibility (WCAG 2.1 AA — required)

Re-check every new brand color pairing before locking the final hex:

| Pairing | Requirement |
|---------|-------------|
| Body text on background | ≥ 4.5:1 |
| Large text / UI components | ≥ 3:1 |
| White label on Brand Indigo button | ≥ 4.5:1 (verify) |
| Brand Indigo text on white / `indigo-50` | ≥ 4.5:1 (verify) |
| Focus ring visibility | clearly visible on light + tinted bg |

`indigo-700` on white passes for text; **white-on-indigo-700 button labels and
indigo-on-indigo-50 must be confirmed**. If a pairing fails, shift Brand Indigo
one step (e.g. `indigo-800`) rather than weakening contrast.

---

## Global Do / Don't

| ✅ Do | ❌ Don't |
|-------|----------|
| Use Brand Indigo for identity + interaction | Reuse status colors as brand/decoration |
| Keep emerald/red/amber for classification only | Introduce a second brand hue |
| Render measurements in mono | Use mono for prose |
| Lead verdicts with classification + number | Use adjectives where a number works |
| Credit OUCRU subtly (footer/about) | Frame product as institutional-only |
| Keep waveform imagery abstract | Depict a realistic diagnostic trace |
| Name degraded/fallback states | Silently hide reduced capability |

---

## Brand Change Governance

When changing anything brand-related:
1. Read `00-index.md` non-negotiables first.
2. Update the relevant branding file **and** `docs/design-guidelines.md`
   (keep tokens in sync).
3. Re-run the AA contrast check if colors changed.
4. Log the change in `docs/project-changelog.md`.
5. Bump the version table in `00-index.md`.

---

## Success Metrics

- Single cohesive primary hue across the product (zero stray `blue-500`).
- All status/neutral semantics preserved (no clinical-meaning regressions).
- WCAG 2.1 AA pass on all new brand color pairings.
- Verdict surfaces lead with classification + number in 100% of states.
- Chatbot refuses ungrounded queries with the evidence-offer pattern
  (QA-testable).

---

## Open Decisions

| # | Decision | Status | Note |
|---|----------|--------|------|
| 1 | Final Brand Indigo hex | Proposed `#4338ca` | May shift ±1 step after AA audit |
| 2 | Mono family | Open | IBM Plex Mono vs JetBrains Mono |
| 3 | Dark mode scope | Deferred | Brand Ink base defined; not yet in product |
| 4 | Logo production | Open | In-house vs commissioned designer |
| 5 | External-launch name | Deferred | Re-open "OUCRU Vital Agent" only if launching beyond OUCRU |

---

## Next Steps

1. Lock final Brand Indigo hex after contrast audit.
2. Choose mono family.
3. Commission/iterate the logo mark from the brief in `02-visual-identity.md`.
4. Execute the token migration (above).
5. Wire the microcopy library into product copy + chatbot system prompt.
6. Sync `docs/design-guidelines.md` and log in changelog.
