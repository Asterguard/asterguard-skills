# Example — Black-box agent: profile and red-team, no code, no server

The flagship composition: a security engineer assesses a running agent they have **no source for**,
entirely from their own harness, with AsterVault (run by AsterGuard) as the only backend. Shows how
the skills compose and where the client/server boundary sits.

## Goal

Given a live agent endpoint, produce a risk report — attack surface, findings, ARS — without reading
code and without shipping any AsterGuard knowledge to the client.

## Setup — install the skills

**Claude Code:**

```text
/plugin marketplace add Asterguard/asterguard-skills
/plugin install asterguard-security@asterguard-marketplace
```

**Cursor / Codex / other harnesses**, plus the scanners and offline-vs-connected mode, are in the shared
**[examples/SETUP.md](../SETUP.md)**. This example profiles a *live* agent, so it uses connected mode (the
AsterVault proxy + MCP); set `ASTERVAULT_MCP_URL` per that doc.

## Pipeline

```
scope (traffic source)
  └─ proxy-recon ───────────► route the agent through AsterVault's proxy; recon = the audit trail
       └─ agent-profiling ──► AI-BOM + authority boundaries from recorded tool-calls
            └─ data-flow ───► stores/fields the tools touch → movers → endpoints
                 └─ information-flow ─► integrity/confidentiality flows + missing controls
                      └─ weakness-graph ─► resolve findings (AsterVault registry.resolve/controls.map)
                           ├─ dast-generation ──► grounded dynamic probes (testgen.patterns)
                           └─ behavioral-redteam ► multi-turn crescendo/boundary/injection
                                └─ security-judge ─► broke/held + findings (LLM-as-judge)
                                     └─ risk-report ─► HTML Artifact (graph.enrich + risk.score)
```

## What stays local vs goes to AsterVault

- **Local:** the recorded traffic, the structural graph, the test specs/transcripts, the rendered report.
- **AsterVault MCP (ours):** weakness resolution, control crosswalk, attack-surface enrichment, ARS,
  attack-pattern corpus. The client never receives the registry or the crosswalk — only per-call answers.

## Success criteria

- A graph built to `docs/graph-schema.md` with agent/tool/store/flow nodes — from traffic only.
- At least one violating information-flow identified (e.g. an effectful tool reachable by an
  untrusted input, or a regulated store reachable by an over-broad identity).
- A behavioral suite that breaks at least one boundary, judged with evidence.
- A report whose ARS and attack-surface facets match what AsterVault would show server-side.

## Why it matters

This is the demo *and* the proof of the model: expert AppSec on a black-box agent, run from the
engineer's own Claude/Codex, with IP and data both staying where they belong.
