# Engagement store — event, engagement, and context shapes

Local-first at `./.asterguard/engagements/<target>/`. `<target>` is a stable id for the app/agent
(repo URL slug, image ref, or a given engagement name). Three files; `context.json` is always rebuildable
from `events.jsonl`.

## `engagement.json`

```jsonc
{
  "id": "eng_7f3a…",                 // stable engagement id
  "target": { "kind": "repo|image|agent", "ref": "github.com/org/app", "name": "sales-copilot" },
  "scope": { "mode": "full|diff", "paths": [] },
  "status": "active",                // active | paused | closed
  "created_at": "2026-11-16T18:40:00Z",
  "updated_at": "2026-11-16T19:02:00Z",
  "counters": { "runs": 7, "events": 214, "open_findings": 9, "proven_breaks": 2, "waivers": 3 },
  "context_ref": "context.json",
  "graph_ref": "graph.json",          // latest local graph; or a knowledge-store pointer when synced
  "last_commit": "a1b2c3d",
  "synced_at": "2026-11-16T19:02:05Z" // last memory.capture to the knowledge store
}
```

## `events.jsonl` — one typed event per line (the history)

Common envelope on every event:

```jsonc
{
  "id": "ev_01J…",            // monotonic / ULID
  "engagement_id": "eng_7f3a…",
  "ts": "2026-11-16T18:55:12Z",
  "harness": "claude-code|codex|ci",
  "actor": "dev@org|agent",
  "run_id": "run_5c…",         // groups events from one security run
  "commit": "a1b2c3d",         // optional; the code state the event is about
  "kind": "finding_opened",
  "weakness_id": "llm_ctx_tool_output_as_instruction",  // when applicable
  "control_id": "soc2:CC6.1",                            // when applicable
  "severity": "high",                                    // when applicable
  "ref": "handler.py:42",                                // location / artifact pointer (local only)
  "provenance": { "skill": "pr-gate", "tool": "registry.resolve", "audit_id": "…" },
  "data": { }                   // kind-specific payload
}
```

Kinds and their `data`:

| `kind` | `data` |
|---|---|
| `run_started` | `{ run_type: "review|pr-gate|episode|scan", scope }` |
| `run_ended` | `{ run_type, outcome, duration_ms }` |
| `scan_completed` | `{ lanes: {...}, counts_by_severity: {...}, sbom_ref }` |
| `finding_opened` | `{ title, lane, cwe, first_seen_commit }` |
| `finding_closed` | `{ reason: "fixed|gone|superseded", closed_commit }` |
| `test_run` | `{ test_id, type: "dast|behavioral|static", result: "pass|fail|inconclusive" }` |
| `canary_hit` | `{ episode_id, token_id, encoding, source: "scan|egress", evidence }` |
| `verdict` | `{ path, verdict: "broke|held|inconclusive", rationale_ref }` |
| `decision` | `{ what, by, rationale }` |
| `waiver` | `{ reason, by, scope: "finding|weakness", expires? }` |
| `policy_recommended` | `{ bundle_ref, targets: [weakness_id] }` |
| `policy_applied` | `{ bundle_ref, approved: true, where: "runtimevault" }` |
| `gate_verdict` | `{ verdict: "PASS|FAIL|WARN", blockers: [weakness_id], delta }` |
| `note` | `{ text }` |

Only structural fields (`kind`, ids, `weakness_id`, `control_id`, `severity`, `data` scalars, graph
topology) sync to the knowledge store. `ref` and any code-bearing `evidence` stay local.

## `context.json` — the fold (current state)

```jsonc
{
  "built_from_event": "ev_01J…",     // high-water mark; re-fold is incremental from here
  "open_findings": [ { "weakness_id", "ref", "severity", "first_seen_commit", "controls": [] } ],
  "proven_breaks": [ { "weakness_id", "episode_id", "evidence", "since_commit" } ],
  "waivers":       [ { "weakness_id", "scope", "reason", "by", "expires?" } ],
  "controls":      { "applied": [], "recommended": [] },
  "posture":       { "summary": "...", "counts_by_severity": {}, "risk": "harness-composed, not ARS-model" },
  "baseline":      { "commit": "a1b2c3d", "scan_event": "ev_…" },
  "graph_ref":     "graph.json",
  "timeline":      [ /* last N events, newest first */ ]
}
```

## Fold rules (deterministic)

1. Replay `events.jsonl` (from `built_from_event` for an incremental update).
2. `open_findings` = `finding_opened` keyed by `(weakness_id, ref)`, minus any later `finding_closed` for
   that key.
3. `proven_breaks` = `canary_hit` and `verdict:broke`, minus a later `finding_closed`/`verdict:held` for
   the same path.
4. `waivers` = active `waiver` records (drop expired).
5. `controls.applied` = `policy_applied`; `controls.recommended` = `policy_recommended` not yet applied.
6. `baseline` = the latest `scan_completed` + its commit.
7. `posture` = roll up severities + the harness-composed risk from `risk-context` (no ARS model is run).

The fold is pure: same events → same context. That is what makes the engagement auditable and lets any
harness rebuild the context from the log alone.
