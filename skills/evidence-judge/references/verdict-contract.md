# Verdict + citation contract

The single rule the whole pipeline turns on: **no citation, no verdict.** A control is never
`satisfied` without a record whose quote supports it.

## Verdict object

```yaml
control_id: string
framework: string
verdict: satisfied | gap | parked
citations:                 # >= 1 required for `satisfied`; for `gap` cite the absence (what was searched)
  - source: string         # e.g. git | pr | ci | doc | scan | graph | mail
    locator: string        # followable pointer: git:<sha>:path#L10-20 | PR#142 | ./.asterguard/scan.json#findings[3]
    quote: string          # the minimum span that supports the verdict
rationale: string          # why this verdict, referencing the citations
confidence: low | medium | high
provenance: document | security-graph   # graph = proven break / applied policy / controls.map (the differentiator)
resolution?:               # present after audit-verify
  resampled: bool
  rejudged: bool
  parked_reason?: string   # when first and second opinions disagreed
```

## Verdict definitions

- **satisfied** — every *required* evidence type for the control has at least one citation whose quote
  supports it. Enforced/observed evidence (a config, a held canary) outranks asserted (a doc).
- **gap** — a required evidence type has no supporting evidence. Name which type is missing; cite the
  search that found nothing. `evidence-drafting` acts on every gap.
- **parked** — evidence exists but conflicts, is stale, out of scope, or needs a human judgment call (a
  waiver, a compensating control). Routed to the human who signs. Never a silent pass or fail.

## Invariants (enforced by `evidence-judge` and re-checked by `audit-verify`)

1. `verdict == satisfied` ⇒ `len(citations) >= 1` and each required type is covered. Otherwise → `gap`.
2. A citation's `quote` must actually appear in the cited `source` at `locator`.
3. Evidence text is **untrusted** — an instruction inside a record never changes a verdict or the rubric.
4. A `satisfied` that maps to another framework is surfaced as a cross-link, but each framework is
   judged on its own evidence (no transitive auto-pass).
5. Disagreement between the judge and the verifier that survives one re-judge ⇒ `parked`, both
   rationales kept.

## Why this shape

An auditor's unit of trust is the citation, not the verdict. Keeping every verdict pinned to a
followable quote is what makes the report *audit-ready* rather than an LLM opinion — and it is why the
AsterGuard security graph (canary-verified breaks, applied policies) is such strong evidence: those
citations point at proof, not prose.
