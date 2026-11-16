---
name: security-engineer
description: Orchestrates a local, agent-native application-security assessment of an AI agent or app — perform the scan, build the SCA/data-flow/information-flow/weakness graphs, generate and judge DAST + behavioral tests, and report. Use when a security engineer asks to assess, profile, scan, or red-team a target (a repo, a container image, or a live agent) without a hosted backend.
---

# Security Engineer (orchestrator)

Run a full AppSec assessment locally, composing the AsterGuard capability skills. The target is a
**repo path**, a **container image ref**, or a **live agent endpoint**; the deliverable is a risk
report backed by a security graph that is byte-compatible with the AsterGuard platform.

## When to Activate

- A security engineer asks to "assess / scan / profile / red-team" an agent or app.
- The request is for local or offline analysis (no AsterGuard server, air-gapped, on a client box).
- Any time two or more of the capability skills below need to run in sequence against one target.

## Core Concepts

The assessment is a staged, idempotent pipeline. Each stage is its own skill; each writes its
artifact to a working directory (`./.asterguard/`) so stages are cacheable, resumable, and
inspectable. Build **every** graph to the shared schema (see `graph-schema.md`) so nothing has to be
re-derived to push results to the platform later. The harness model does the analysis and judging —
there is no server call.

## The pipeline

1. **Recall + scope.** First `knowledge-recall` pulls the common knowledge + prior memory for this
   app/area (approved patterns, past findings/fixes/decisions/waivers) so the work starts informed.
   Then decide source type: `code` (repo), `infra` (image/IaC), or `traffic` (live agent) — this picks
   which collectors and graph skills run.
2. **Collect** — `local-scan` (SCA/IaC/secrets/AI-BOM on a repo or image) and/or `proxy-recon`
   (record a live agent). Bootstrap any missing collector first.
3. **Build the architecture** — compose, writing into one graph:
   - `sca-graph` — dependency tree + CVEs (always, when packages exist)
   - `data-flow` — stores/fields → functions/tools → endpoints
   - `information-flow` — the IFC overlay (integrity/confidentiality flows + missing controls)
   - `weakness-graph` — weakness↔component graph + control crosswalk
   - `agent-profiling` — agent AI-BOM + authority boundaries (for agentic targets)
4. **Test** — `dast-generation` and `behavioral-redteam` emit tests from the graphs
   (same `TestDefinition` schema the platform ingests).
5. **Red-team episode** — for agent targets, run the attacker/defender/verifier harness
   (`behavioral-redteam`) with `canary-testing`: plant fresh canaries, drive the attack with a
   concurrent benign task (utility under attack), and let AsterVault's egress + audit be the
   independent verifier. A canary hit is hard, code-checkable proof.
6. **Run & judge** — drive tests (through the proxy or a local driver); `security-judge` scores
   broke/held → findings, with canary hits as the hard evidence and safety metrics (ASR@budget,
   utility-under-attack, severity-weighted violations, detection rate).
7. **Remediate** — `remediation` turns the findings (esp. exfil / over-privilege) into enforceable,
   least-privilege policy-as-code (SPIFFE, IAM, egress allowlists, OPA/Cedar, the AsterVault PDP, …),
   grounded in the graph's allow-set; optionally enforced at the gateway.
8. **Report** — `risk-report` folds findings + graph + remediations into the attack-surface facets and
   emits an HTML Artifact.
9. **Capture** — `memory-capture` writes the decisions, findings, fixes and waivers (with the *why*)
   back to the team memory, so the next task on this app starts informed. The loop closes.

## Practical Guidance

- **Source-type branch (low freedom):** `code` → full pipeline incl. SAST-style weakness mapping;
  `infra` → skip code/data-flow-from-AST, derive reach from IAM + image contents; `traffic` →
  build the graph from recorded tool calls and responses, no code parsing.
- **Fail-open collection (medium freedom):** a missing collector degrades that lane, never the run.
- **One graph, many writers:** each graph skill *adds* nodes/edges to the same envelope; never fork
  a second graph for the same target.
- Keep each stage's output in `./.asterguard/<stage>.json` and reference by path, not by inlining
  large payloads into context (see the context-optimization substrate skill).

## Integration

- knowledge-recall, memory-capture — the common-knowledge + memory bookends (recall first, capture last)
- local-scan, proxy-recon — collection
- sca-graph, data-flow, information-flow, weakness-graph, agent-profiling — architecture
- dast-generation, behavioral-redteam (orchestrates attacker/defender/judge), canary-testing, security-judge — testing
- remediation — fix as least-privilege policy-as-code (SPIFFE/IAM/egress/OPA/Cedar/PDP/…)
- risk-report — output
- Substrate (from the context-engineering collection): multi-agent-patterns (parallel lane agents),
  advanced-evaluation (the judge), context-optimization (large-graph context), memory-systems
  (the graph as file/graph memory).

## References

- [Graph schema (SSOT)](../../docs/graph-schema.md)
- [Flagship example](../../examples/blackbox-agent-redteam/PRD.md)
