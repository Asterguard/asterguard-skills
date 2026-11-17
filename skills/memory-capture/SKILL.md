---
name: memory-capture
description: At the end of a session, PR, or assessment, distill the outcomes — decisions, findings, fixes, review verdicts, waivers and the reasoning behind them — and write them to the team's shared memory so future work starts informed. Use when wrapping up a task whose outcome should compound for the next agent.
---

# Memory Capture

Close the loop: what was decided, fixed, found, or waived — and *why* — becomes durable, team-shared
memory in the AsterVault gateway, so the next session recalls it instead of relearning. This is the
"self-improving" half; recall reads what this writes.

## When to Activate

- At the **end** of a session / PR / assessment whose outcome matters later.
- After a review, a remediation, or a decision/waiver worth remembering.
- Whenever the engineer says "remember that / note for next time".

## Core Concepts

- **Capture the decision and the why, not the transcript.** A future agent needs the reasoning and the
  resolution, not raw logs.
- **Scoped + provenanced:** every record carries app / team / weakness / topic and its provenance
  (session / PR / commit), tenant/team-scoped so it's shared with the team and no one else.
- **Kinds:** `decision`, `finding`, `fix`, `review`, `waiver`. A record is one of these, high-signal.
- **Promotion:** a durable, reusable record can graduate into the knowledge plane (an approved pattern)
  — but only **review-gated** (a human curates before it becomes org knowledge).

## Method

1. At wrap-up, identify what's worth remembering: decisions made, findings + how they resolved,
   fixes/remediations (and the policy that closed them), review verdicts, waivers (with justification).
2. `memory.capture(record)` for each — scoped (app/team/weakness/topic) with provenance and the *why*.
3. For something reusable (a pattern other work should follow), `memory.promote(memory_id, approved)`
   after review → it becomes an approved pattern in the knowledge plane.
4. Keep it lean: a handful of high-signal records, not a running log.

## Practical Guidance

- **Write the why** — the reasoning is what survives and makes a recall useful; a bare "fixed it" doesn't.
- **Don't write inferences as facts** — capture what was decided/observed, not a guess.
- **A waiver is a decision record** — the justification and its scope, so a future recall can honor or
  revisit it, never a silent exception.
- **Keep PII/secrets out of memory** — reference the finding, don't store the sensitive value.
- **Promotion is curated** — never auto-promote; a human approves what becomes shared knowledge.

## Integration

- security-judge, remediation, risk-report — their outcomes are what gets captured
- knowledge-recall — reads these records at the next task's start
- security-engineer — capture is the final step of the pipeline
- AsterVault `memory.capture` / `memory.promote`
- **Where it persists (gateway-side):** the records land in the gateway's store — **SQLite** for a
  single box or pilot, **Postgres** for team-shared, durable, multi-node memory (same `memory.*` calls
  either way). See `../../docs/MCP_WIRING.md`.

## References

- [AsterVault MCP tools](../weakness-graph/references/astervault-tools.md)
- [Two-sided architecture](../../docs/ARCHITECTURE.md)
