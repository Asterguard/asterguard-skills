# Runbook guidelines

Guidelines for creating, maintaining, and executing the operational runbook skills in this pack. They
adapt the `adk_runbooks` runbook discipline to AsterGuard's harness-portable, gateway-backed model.
Pair this with [RUNBOOKS.md](RUNBOOKS.md) (the SSOT + binding map) and
[`template/runbook-template.md`](../template/runbook-template.md).

## General principles

- **Clarity under pressure.** A responder runs this mid-incident. Short imperative steps, no prose
  padding, decisions called out explicitly.
- **Accuracy.** Every tool, parameter, and expected output must match the real AsterVault surface
  (see the binding map). Never reference a Chronicle/GTI/SOAR tool — those are retired.
- **Consistency.** Same section order, same `${VARIABLE}` input style, same artifact paths
  (`./.asterguard/…`) across every runbook.
- **Actionability.** Concrete steps and the decisions a responder must make — not background essays.
- **Reproducible + auditable.** A runbook names what it read, what it decided, and (connected) the
  `audit_id` of each metered call, so a run can be replayed and graded by the `evals` skill.

## Structure (every runbook)

- **When to Activate** — the triggers (mirror the `description`).
- **Objective** — the single goal.
- **Scope** — what's in and explicitly out of bounds.
- **Inputs** — required to start, `${VARIABLE}` form, with the source of each (alert field, prior
  runbook output, engagement context).
- **Outputs** — the structured results handed back to the caller.
- **Tools** — the AsterVault gateway tools and the sibling skills it composes. Separate the
  **client-side** work (analysis, graph build, judgment) from the **gateway** call (grounding,
  metering, canary/audit verification).
- **Workflow Steps & Diagram** — numbered steps **and** a `mermaid` diagram of what was actually
  performed, showing the Analyst/Agent ↔ skills ↔ gateway tools. Artifacts render ` ```mermaid ` fences
  natively — do not load a library.
- **Decision Logic / Completion Criteria** — routes/verdicts and how "done" is decided.
- **Integration** — the atomic/common/sibling skills it builds on.

IR playbooks also carry the **PICERL** phases (Preparation, Identification, Containment, Eradication,
Recovery, Lessons-learned).

## The three layers (progressive disclosure)

1. **Atomic** (`skills/atom-*`) — one gateway tool, one job, typed inputs/outputs, decision hints. The
   leaves. Keep them short (atomic template form).
2. **Common** (`enrich-indicator`, `record-in-engagement`, …) — reusable multi-step building blocks
   that compose atomics. Called by many workflows; never duplicated inside one.
3. **Workflows** (triage / investigation / hunting / detection / IRP / reporting) — compose common +
   atomic steps into a named operation. They *order* building blocks; they never re-implement one.

A workflow that needs to enrich an indicator calls `enrich-indicator`; it does not inline the
`registry.resolve` + `graph.enrich` + `memory.recall` calls.

## Engagement & memory (never hand-roll state)

- **Open first, checkpoint last.** Start by `open`ing the engagement (loads folded context + history);
  end by `checkpoint`ing the typed events the run produced. Use the `engagement` skill.
- **The case is the engagement.** There is no SOAR case object — the long-lived engagement per target
  is the case; comments/dispositions are typed events (`finding_opened`, `verdict`, `decision`,
  `waiver`, `gate_verdict`, `note`, …).
- **Structural-only sync.** Full detail (with code refs) stays local in `./.asterguard/`; only
  structural records cross to shared memory via `memory-capture`. Never ship raw code or data.

## Connected vs offline (state both)

- **Offline** — harness + skill Markdown + local collectors only. Grounding (`registry`/`graph`/
  `knowledge`) degrades to local pack data or is noted as unavailable; the run still completes. No ARS
  token, no quota.
- **Connected** — `ASTERVAULT_MCP_URL` set. Grounding, shared memory, canary/egress verification, and
  metering are live. Every metered `scan`/`run`/grounding call carries `X-ARS-Token` (via `ars-token`)
  and returns an `audit_id` to record. A runbook degrades a lane on failure; it never blocks the run.

## Human-in-the-loop (dual-use discipline)

Any **state-changing or containment** action (block egress, revoke a token, isolate a runtime, apply a
policy, close a finding) routes through `confirm-action` first and is recorded as a `decision` event.
Red-team/offensive runbooks run on **authorized engagements only** and record the authorization in the
engagement; attacker-model selection and ASR are recorded per the offensive-security doc.

## Reporting requirement

If a runbook produces a report, the report **must** name the runbook used at the top
(`**Runbook Used:** <skill name>`), per the source discipline — so a reader (and the `evals` rubric)
can trace output to procedure.

## Maintenance

- Review runbooks when the gateway tool surface, the pack schema, or the engagement event schema
  changes. Keep the binding map in [RUNBOOKS.md](RUNBOOKS.md) current.
- A new runbook is not done until an `evals` dataset case exists for it (trajectory + schema + rubric),
  so regressions are caught.
