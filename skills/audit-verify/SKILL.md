---
name: audit-verify
description: Independently second-opinion the evidence-judge verdicts — re-check every gap and a sample of the satisfied verdicts against the cited evidence, allow one re-judge, and park any disagreement for human review instead of silently flipping it. Use after evidence-judge, before the audit report, to harden the verdicts against self-grading bias.
---

# Audit Verify

A compliance review that grades its own work is suspect. `audit-verify` is the independent check: a
fresh pass that does not trust the first verdict, only the **cited evidence**. It mirrors the
adversarial-verify step in the security review — confirm from evidence, or park.

## When to Activate

- After `evidence-judge`, before `audit-report`.
- Any time verdicts must be hardened before a human signs.

## Method

1. **Re-check every `gap`** — did the first pass miss evidence that exists? Re-retrieve with different
   queries. A gap that was real stays a gap (now double-confirmed); a gap that had evidence becomes a
   candidate `satisfied` → one **re-judge**.
2. **Sample the `satisfied`** — independently verify that each sampled control's citations actually
   support it. Pull the quote, read it cold, decide if it proves the required evidence type. Bias the
   sample toward high-impact controls and low-confidence verdicts.
3. **One re-judge only.** If the second opinion disagrees with the first, re-run the judge once with
   both opinions as input. If they still disagree → **parked for human review**, with both rationales
   recorded. Never silently flip a verdict.
4. **Independence:** verify from the evidence and the oracle, not from the first rationale. Treat the
   first verdict as a claim to test, not a starting point to confirm.
5. Write `./.asterguard/compliance/verified.<framework>.json` (final verdicts + which were resampled,
   re-judged, or parked).

## Practical Guidance

- **Park is a feature, not a failure:** a parked control routes a real judgment call to the human who
  signs — that is the point of "no certification without a signature".
- **Record the disagreement:** when first and second opinions differ, keep both; auditors value the
  dissent trail.
- **Cheap when connected:** use a different model/route for the second opinion if available, so the
  check isn't the same model marking its own homework.

## Integration

- Consumes `evidence-judge` verdicts; its verified output is what `audit-report` renders and
  `memory-capture` stores.

## References

- [Verdict + citation contract](../evidence-judge/references/verdict-contract.md)
