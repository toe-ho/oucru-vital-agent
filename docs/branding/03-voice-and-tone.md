# 03 — Voice & Tone

**Last Updated:** 2026-05-30

Voice is a **trust instrument**, not decoration. The product's value is honest,
auditable verdicts — the way it speaks must reinforce that.

---

## Three Principles (apply everywhere)

1. **Calibrated, never overconfident.** Mirror the "uncomputable" class.
   Surface the *why* and the *number*.
2. **Verdict first, evidence second.** Clinicians scan. Lead with the
   classification, then the SQI that drove it.
3. **Grounded analyst, not chatbot.** Cite segments/reports, refuse ungrounded
   claims, never give clinical advice or role-play a clinician.

---

## The Split-Voice Model

| Layer | Surfaces | Personality | Goal |
|-------|----------|-------------|------|
| **Shell** | Landing, docs, onboarding, marketing, about | Warm, confident, plain English | Memorability, approachability |
| **Core** | Verdict surfaces: timeline, badges, reports, chat answers | Near-zero personality; neutral + evidence-first | Perceived neutrality = trust |

Personality lives in the **shell**. It evaporates inside the **core** where
users are judging machine output.

### Shell voice examples

> ✅ "Know which signals you can trust — in minutes, with the evidence behind every call."
>
> ❌ "Leverage agentic AI to revolutionize your signal QA workflow."

- Short sentences. Benefit-led. Concrete.
- Confident without hype. No "revolutionize", "seamless", "powerful AI".

### Core voice examples

> ✅ "Reject — HRV 0.42 (below 0.70 threshold)."
>
> ❌ "Bad signal!"

- State the verdict, then the metric + threshold.
- No exclamation. No adjectives where a number works.

---

## Microcopy Library

| Situation | ✅ Do | ❌ Don't |
|-----------|-------|----------|
| Verdict (reject) | "Reject — HRV 0.42 (below 0.70 threshold)." | "Bad signal!" |
| Verdict (accept) | "Accept — all 8 SQI metrics above threshold." | "Looks great!" |
| Uncertainty | "Uncomputable — insufficient clean beats to score." | "We couldn't figure this out." |
| Stale report | "Report is stale: overrides postdate generation. Regenerate to refresh." | "Oops, this is out of date!" |
| Empty state | "No recordings yet. Upload a CSV or Parquet file to begin." | "Nothing here! 🤷" |
| Error (system) | "Assessment failed to start. The signal service is unavailable — retry shortly." | "Something went wrong!" |
| LLM fallback | "Generated with rule-based classification (assistant unavailable)." | (silent — never hide degraded mode) |
| Chat refusal (no data) | "I don't have data for that recording in this assessment." | "I think it's probably fine." |
| Chat refusal (scope) | "That's a clinical judgment outside my scope. I can show the SQI evidence." | Any diagnosis or advice. |

### Writing rules
- **Numbers in mono, prose in Inter** (see visual identity).
- Reference segments/metrics by their real names (e.g. "HRV", "segment 14"),
  not vague terms.
- Never invent reassurance. If degraded (fallback, partial), say so.

---

## Chatbot Persona Spec

| Field | Spec |
|-------|------|
| **Name** | "Vital Agent" |
| **Role** | Grounded analyst over persisted assessment data |
| **Always** | Cite segment/report sources; quote scores + thresholds; state limits |
| **Never** | Invent data, give clinical advice, diagnose, role-play a doctor, claim certainty beyond SQI |
| **Refusal default** | When ungrounded → say so plainly, then offer the evidence it *does* have |
| **Tone** | Core voice — neutral, evidence-first, calm |

### Refusal pattern (template)

> "I don't have [X] in this assessment. Here's what I can show: [grounded
> evidence — segments, SQI scores, thresholds]."

### Scope boundary (template)

> "That's a clinical judgment outside my scope. I can show the SQI evidence and
> the segment classifications — the interpretation is yours."

---

## Quick Checklist (per string)

- [ ] Right layer? (shell = warm / core = neutral)
- [ ] Verdict before evidence?
- [ ] Number + threshold present where relevant?
- [ ] No hype words, no false reassurance?
- [ ] Degraded/uncertain states named honestly?
- [ ] Chatbot: cited or refused — never guessed?
