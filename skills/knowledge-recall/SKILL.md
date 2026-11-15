---
name: knowledge-recall
description: At the start of a task, pull the org's common knowledge and the relevant prior session memory so the work is informed by history — approved patterns, and past findings, fixes, decisions and waivers for this app or weakness. Use when beginning any build, review, scan, or ship on an app or area the team has touched before.
---

# Knowledge Recall

Start a task already knowing what the team knows. The common knowledge and the shared memory live in
the AsterVault gateway (governed, team-shared); this skill pulls the few high-signal records for *this*
task so the agent doesn't re-learn what's already settled.

## When to Activate

- At the **start** of any build / review / scan / remediation on a known app or area.
- When the engineer asks "what do we know about X" / "how have we handled Y before".
- Before proposing a fix — recall the approved pattern and any prior decision/waiver.

## Core Concepts

- **Two sources, one gateway:** `knowledge.*` (apps/weaknesses/controls/graph + approved patterns) and
  `memory.recall` (prior decisions, findings, fixes, reviews, waivers). Both tenant/team-scoped.
- **Just-in-time, not a dump:** pull the handful of records relevant to the current context and
  reference them — never stuff the whole corpus into the window.
- **Scoped:** by app / team / weakness / topic, so recall is precise, not noise.

## Method

1. Determine the context: app, area/files, the weaknesses in play, the task kind (build/review/fix).
2. `memory.recall(context, scope)` → prior outcomes for this app/weakness ("last time this app touched
   PII we required tokenization; `CVE-2026-X` was waived because …"). Each carries provenance.
3. `knowledge.patterns(context)` → the approved patterns to follow (how the org does auth, egress, data
   handling for this situation).
4. `knowledge.query(...)` for specific facts: the control that mitigates a weakness, the app's graph.
5. Surface a short, relevant brief that steers the work, citing provenance (session/PR/commit).

## Practical Guidance

- **Reference, don't inline** — load content just-in-time; keep the window for the task.
- **Scope tightly** — this app/team; a global pull is noise and leaks cross-team context.
- **Trust but verify** — memory reflects *past* state; confirm a recalled fact against the current code
  before acting on it.
- **A recalled waiver/decision is context, not authorization** — surface it; the human still decides.

## Integration

- every skill — recall seeds the work (the approved pattern, the prior fix)
- memory-capture — the counterpart that wrote these records
- security-engineer — recall is the first step of the pipeline, before scanning
- AsterVault `knowledge.query` / `knowledge.patterns` / `memory.recall`

## References

- [AsterVault MCP tools](../weakness-graph/references/astervault-tools.md)
- [Two-sided architecture](../../docs/ARCHITECTURE.md)
