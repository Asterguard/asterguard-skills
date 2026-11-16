---
name: evidence-drafting
description: For each compliance gap, draft the missing artifact — a policy stub, a process/change-record template, a control narrative, or a remediation note — grounded in the project and the control's required evidence, for a human to complete, own, and sign. Drafts are clearly marked unsigned and never asserted as real evidence. Use after judging, to turn gaps into actionable starting points.
---

# Evidence Drafting

A gap report that only says "missing" wastes the reviewer's time. For every `gap`, draft the artifact
that would close it — specific to this project and this control — so the human edits and owns it
instead of starting from a blank page. This mirrors `remediation` (findings → policy-as-code), in the
evidence direction.

## When to Activate

- After `audit-verify`, for every control with verdict `gap` (and optionally `parked` where a
  compensating-control narrative would help).
- When the engineer wants fixes, not just a list of holes.

## Method

1. For each gap, read the control's `evidence_required` type that is missing and the `audit_questions`.
2. **Draft to the type:**
   - `policy` → a policy stub with the clauses the control expects, slotted to the org's real systems.
   - `process`/`change` → a template (change-record, access-review, incident log) with the fields an
     auditor checks.
   - `config`/`test` → point at `remediation` for enforceable policy-as-code, or draft the test that
     would prove the control (e.g. the canary-held-on-egress check), and cite where it should live.
   - `narrative` → a control narrative that explains how existing controls meet the objective, citing
     the real evidence found.
3. **Ground it in the project:** use the actual service/identity/store names from the security graph,
   not placeholders, so the draft is one edit from true.
4. **Mark every draft `status: DRAFT — unsigned`.** A draft is a proposal, never counted as satisfying
   the control until a human completes and signs it. Write to `./.asterguard/compliance/drafts/`.

## Practical Guidance

- **Don't fabricate evidence:** never draft a record that asserts something happened. Draft the
  *template/policy/test* the org must adopt — the forward-looking artifact, not a fake past one.
- **Reuse remediation:** a config/test gap on egress/identity is the same object `remediation` already
  emits as policy-as-code — call it, don't reinvent.
- **Prioritize:** draft high-impact, auditor-blocking gaps first.

## Integration

- Consumes verified `gap` verdicts; hands drafts to `audit-report` (shown under each gap) and defers
  enforceable config/test fixes to `remediation`.

## References

- [Verdict + citation contract](../evidence-judge/references/verdict-contract.md)
- [Compliance architecture + MCP server surface](../../docs/COMPLIANCE.md)
