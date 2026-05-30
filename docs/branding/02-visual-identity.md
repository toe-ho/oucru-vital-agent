# 02 — Visual Identity ("Instrument")

**Last Updated:** 2026-05-30

Direction: **Instrument** — the feel of a precision medical instrument / good
oscilloscope. Calm, exact, engineered. Warmth is delivered by *voice*, not by
visual flourish.

---

## Color

### Identity Axis — Brand Indigo

A single identity hue, deliberately chosen to **never collide** with the
clinical status palette (green/red/amber) or the legacy interactive blue.

| Token | Hex | Tailwind | Role |
|-------|-----|----------|------|
| **Brand Indigo** | `#4338ca` | `indigo-700` | Primary identity **and** primary interactive (replaces legacy `blue-500`) |
| **Indigo Hover** | `#3730a3` | `indigo-800` | Hover / active / pressed states |
| **Brand Ink** | `#1e1b4b` | `indigo-950` | Logo on light, deep headers, dark-surface base |
| **Indigo Tint** | `#eef2ff` | `indigo-50` | Selected rows, subtle brand fills, focus halos |

> **Decision:** retire `blue-500` as the interactive primary; promote Brand
> Indigo. One identity hue = stronger recognition + less palette sprawl.
> The final hex may shift one step lighter/darker pending the AA audit
> (see `04-application-and-governance.md`).

### Status Colors — DO NOT CHANGE

These carry clinical meaning. Reserved exclusively for classification state.

| Status | Hex | Tailwind | Meaning |
|--------|-----|----------|---------|
| Accept | `#10b981` | `emerald-500` | Segment passed QA |
| Reject | `#ef4444` | `red-500` | Segment failed QA |
| Uncomputable | `#f59e0b` | `amber-500` | QA unclear, manual review |
| Stale | `#f59e0b` | `amber-500` | Report outdated by overrides |

### Neutrals — unchanged

Gray scale (`gray-50` … `gray-900`) per `docs/design-guidelines.md`: text,
backgrounds, borders, disabled states.

### Usage Split

- **Brand Indigo** → identity surfaces + interactive affordances (buttons,
  links, focus, active nav, brand headers).
- **Status colors** → classification meaning *only* (badges, timeline, report
  flags). Never decorative.
- **Neutrals** → everything structural.

---

## Typography

Two families. No third.

| Family | Use | Notes |
|--------|-----|-------|
| **Inter** | All UI + body + brand headlines | Keep existing scale from `design-guidelines.md`; weights 400/500/600, plus 700/800 for hero headlines |
| **Mono** (IBM Plex Mono *or* JetBrains Mono — TBD) | Numerals only: SQI scores, thresholds, timestamps, segment IDs | Reinforces instrument precision; aligns columns. Use `tabular-nums`. **Never for prose.** |

**Rule:** any displayed *measurement* (score, threshold, ms, count) renders in
mono; surrounding labels and prose stay Inter.

---

## Logo

### Mark
- A single **abstracted signal peak** (PPG upstroke / QRS-like) drawn as a clean
  monoline geometric glyph.
- The upstroke **resolves into a subtle checkmark or returns cleanly to a
  baseline** = "verified signal."
- Optional faint 2–3 line oscilloscope grid behind the full lockup.
- Single, consistent stroke weight.

### Wordmark
- `Vital Agent` in **Inter SemiBold**.
- `OUCRU` smaller, tracked caps, set above or before the wordmark.

### App Icon / Favicon
- Peak glyph only.
- Brand Indigo on white (light); white on Brand Ink (dark).

### Hard Constraints
- Waveform stays **abstract** — must not resemble a real diagnostic trace or
  imply a clinical reading.
- Maintain clear space ≥ the height of the peak glyph on all sides.
- Do not recolor the mark into a status color.
- Get a designer for the final production mark; this spec is the brief.

---

## Iconography & Data-Viz

- Line icons, single weight, matching the monoline logo language.
- Neutral data-viz strokes use `slate-400`; reserve indigo for brand/interaction
  and status colors strictly for classification.
- Segment timeline keeps its existing status color-coding (accept/reject/
  uncomputable) — brand indigo is used only for selection/hover, never to
  represent a verdict.

---

## Dark Mode

Brand Ink is defined as the dark-surface base, but current product docs are
light-only. **Dark mode is deferred** — treat as later scope (see open
decisions in `04`).
