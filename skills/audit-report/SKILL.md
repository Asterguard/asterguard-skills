---
name: audit-report
description: Render an audit-readiness review as an HTML Artifact — per-control verdicts (satisfied/gap/parked) with their citations, coverage % per framework, the drafted evidence for each gap, and a clear "readiness, not certification; a human signs" banner. Use at the end of the compliance-auditor pipeline to produce the deliverable the reviewer works and signs.
---

# Audit Report

Fold the verified verdicts + citations + drafts into one shareable HTML Artifact, rendered in the
client's harness. The deliverable mirrors `risk-report`: data-driven, local render, no server
round-trip to display.

## When to Activate

- End of the `compliance-auditor` pipeline, once verified verdicts exist.
- The engineer asks for a readiness report, a gap report, or an evidence pack for an auditor.

## Core Concepts — what the report shows

- **Header:** framework + version, coverage % (satisfied / total), and a **readiness, not
  certification** banner — explicitly "a human reviews and signs; from a seed pack if offline".
- **Per-control row:** id · title · verdict pill (satisfied / gap / parked) · the **citation(s)**
  (source + locator + quote, each a followable pointer) · the crosswalk `maps_to` chips.
- **Gaps section:** each gap with which required evidence type is missing and the **drafted artifact**
  (collapsed), marked `DRAFT — unsigned`.
- **Parked section:** the controls needing human judgment, with both opinions when they disagreed.
- **Evidence provenance:** how many verdicts came from the security graph (proven breaks / applied
  policies) vs documents — the AsterGuard differentiator, shown as a small stat.

## Method

1. Read `./.asterguard/compliance/verified.<framework>.json` + `drafts/`.
2. Render to the shared visual grammar (reuse `risk-report`'s tokens/components: pills, cards, mono
   citations). One framework per section when several were audited.
3. Compute coverage and the provenance stat from the verdicts — never hardcode; the report is a view
   over the data.
4. Emit the HTML Artifact; keep every citation copy-pasteable so an auditor can follow it.

## Practical Guidance

- **Never imply certification.** The word is *readiness*. The sign-off is the human's.
- **Citations are the product.** A satisfied row with no visible citation is a bug — surface the quote.
- **Diff-friendly:** when prior memory exists, mark controls that changed since the last cycle
  (newly satisfied, regressed, newly parked).

## Integration

- Consumes `audit-verify` output + `evidence-drafting` drafts; reuses `risk-report`'s rendering grammar.
- The signed result feeds `memory-capture` (accepted evidence + waivers, with the why).

## References

- [Verdict + citation contract](../evidence-judge/references/verdict-contract.md)
- `risk-report` for the shared HTML grammar
