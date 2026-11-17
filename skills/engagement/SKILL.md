---
name: engagement
description: The security engagement's context, history, and session manager — harness-independent and local-first. Opens/resumes a long-lived engagement per target, records a typed security-event stream, folds it into a current context, and feeds contextual decisions to the other skills. Use when starting or finishing any security run, or when a decision needs the target's history (is this finding new, was it waived, did we already prove this path holds) — so work is informed by everything known about the target, not cold-started.
---

# Engagement (context · history · session manager)

A security engagement outlives any single Claude/Codex chat. This skill is the **harness-independent**
layer that remembers a target across runs: it opens/resumes an engagement, records every security run as
a typed **event stream**, folds that history into a **current context**, and hands that context to the
other skills so each run starts informed — and so the system learns what matters for this target.

It is **local-first** (`./.asterguard/engagements/<target>/`, plain files any harness can read) and syncs
only *structural* state to the AsterGuard knowledge store (`memory.*`) for team-shared, cross-box recall.
Nothing here needs a server; the store only makes it shared and durable.

## When to Activate

- **First** step of any run — `security-engineer`, `pr-gate`, `check-planner` all `open` the engagement to
  load context before they plan.
- **Last** step — `checkpoint` the run's events back so the next run (any harness) starts ahead.
- Whenever a decision needs history: "is this finding new or known?", "was this waived, and why?",
  "did we already prove this path holds?"

## Core Concepts

**The session is the engagement, not the chat.** A harness session is ephemeral; the *engagement* is the
long-lived security context for one target (repo / image / live agent), spanning many runs and harnesses.

**Context is a fold of history.** The current picture (open findings, posture, controls, waivers, proven
breaks) is derived by reducing the append-only event log — never hand-maintained, always reproducible.
Append an event; the context updates; nothing is overwritten or lost.

**Structural-only sync.** The local store holds the full detail (with code refs); only structural records
(finding ids, weakness ids, control ids, graph topology, verdicts, waivers) cross to the knowledge store —
never raw code or data. Offline, it is fully functional with nothing leaving the box.

## The object model

Stored at `./.asterguard/engagements/<target>/` (see `references/event-schema.md` for exact shapes):

- **`engagement.json`** — id, target, scope, status (`active|paused|closed`), timestamps, counters, and the
  pointer to the current context + latest graph.
- **`events.jsonl`** — the append-only **history**: one typed security event per line, with provenance
  (harness, run_id, commit, actor, ts).
- **`context.json`** — the **current context**: the cached fold of the events (below). Rebuildable from
  `events.jsonl` at any time.

Event kinds (one schema, typed `kind`): `run_started` · `run_ended` · `scan_completed` ·
`finding_opened` · `finding_closed` · `test_run` · `canary_hit` · `verdict` · `decision` · `waiver` ·
`policy_recommended` · `policy_applied` · `gate_verdict` · `note`.

## Operations (the session verbs)

- **`open(target, scope)`** — create or resume the engagement; load `context.json` + `events.jsonl`, and
  `memory.recall` the structural state from the knowledge store to merge. In **connected mode**
  (`ASTERVAULT_MCP_URL` set), first ensure the org's ARS token via `ars-token` so the run's metered
  scan/run calls are authorized and attributed. Returns the current context.
- **`append(event)`** — write one typed event to `events.jsonl` and re-fold `context.json`.
- **`context()`** — the current folded context a run starts from.
- **`baseline()`** — the reference state for delta decisions (what `pr-gate` calls "new vs backlog"):
  the last checkpointed context + last scanned commit.
- **`checkpoint()`** — `memory.capture` the engagement's structural state (graph, findings summary,
  decisions, waivers) to the knowledge store; mark the run's events durable.
- **`distill()`** — evaluate what worked (which tests found real breaks; which fixes closed them; which
  checks were signal vs noise) and propose promotions.
- **`promote(item)`** — human-gated (`memory.promote`) → a reusable pattern for this and similar targets.
- **`close()` / `pause()`** — set engagement status.

## The context fold (events → current state)

Deterministic reduction over `events.jsonl`:

- `open_findings` = `finding_opened` − `finding_closed` (keyed by weakness_id + location).
- `proven_breaks` = `canary_hit` / `verdict:broke` not since closed.
- `waivers` = active `waiver` records (weakness_id, reason, by, scope).
- `controls` = `policy_applied` + outstanding `policy_recommended`.
- `posture` = the harness-composed risk summary (from `risk-context` features — **no ARS model runs**),
  rolled up; plus severity counts.
- `baseline` = last `scan_completed` + its commit; `graph_ref` = latest captured graph.
- `timeline` = recent events for display / decision context.

## How the other skills use it

- **`check-planner`** reads `context()` — skips paths already proven held, focuses the plan on new/changed
  surface; the standard-checks plan becomes history-aware.
- **`pr-gate`** uses `baseline()` for the delta (new vs backlog), honors `waivers` so the same item does
  not re-block every PR, and uses `proven_breaks` to pre-aim the attacker.
- **`security-engineer`** `open`s at the start, `checkpoint`s at the end; its report is a view (lens) over
  the engagement trace.
- **`knowledge-recall` / `memory-capture`** are the engagement's sync primitives — recall on `open`,
  capture on `checkpoint`.

## Learning loop (contextual security)

`distill()` turns history into judgment: which checks/tests/fixes mattered for this target (and similar
ones), which were noise. Approved learnings (`promote`) steer the next plan — so decisions come from
accumulated context + what's been learned, not a cold start. This is the self-improving flywheel, made
stateful: **run → capture → evaluate → distill → review+approve → reuse.**

## Integration

- **Local store:** `./.asterguard/engagements/<target>/` — harness-independent; any of Claude Code / Codex
  / CI opens the same engagement by target id.
- **Knowledge store (optional, structural only):** `memory.recall` (open), `memory.capture` (checkpoint),
  `memory.promote` (promote).
- **Consumed by:** `check-planner`, `pr-gate`, `security-engineer`.
- **Not** the runtime's session handling — the gateway's credential/grant sessions are a separate concern
  in `asterguard-runtimevault`.

## References

- `references/event-schema.md` — the engagement / event / context shapes and the fold rules.
- `../../docs/RUN_PLAYBOOK.md` — the chain and the knowledge-store persistence model.
