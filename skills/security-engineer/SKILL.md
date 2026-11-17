---
name: security-engineer
description: Orchestrates a local, agent-native application-security assessment of an AI agent or app — perform the scan, build the SCA/data-flow/information-flow/weakness graphs, generate and judge DAST + behavioral tests, and report. Use when a security engineer asks to assess, profile, scan, or red-team a target (a repo, a container image, or a live agent) without a hosted backend.
---

# Security Engineer (orchestrator)

> Realized as the **`full-360`** playbook (`playbooks/full-360.yaml`), run by `playbook-runner`. This
> skill is the named entrypoint; the pipeline below is the playbook's composition as data, so it can be
> customized or overridden per org without editing this skill.

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
4. **Test** — `sast-generation` (target-grounded semgrep rules + static assertions), `dast-generation`
   (dynamic probes) and `behavioral-redteam` emit tests from the graphs (same `TestDefinition` schema
   the platform ingests). SAST and DAST share the `testgen.patterns` corpus, so every CWE gets both a
   static and a runtime test.
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

## Pack enrichment — read the target through its vendor packs

Every stage is grounded in the **packs** for the target's detected vendors (agent-framework / provider /
runtime / harness), so a LangChain app is read and tested *as LangChain*, not generically. `check-planner`
profiles the target and resolves the packs — **connected** via `rules.fetch(profile)` (the MCP serves the
rule content; the client evaluates locally), or **offline** by loading them from disk
(`PluginRegistry.discover` + `ThreatRuleEngine.from_pack`). Each pack ships four facets, and each stage
pulls the one it needs:

| Stage | Pack facet | How it enriches the response |
|---|---|---|
| Recall + scope | the pack set | `rules.fetch(profile)` → a pack-driven plan (which lanes, rules, frameworks) |
| Scan | **static** (`semgrep_rules_path`) + matchers | run the pack's SAST rules; its include/exclude scope the files |
| Build architecture | **how-to-read** (`system_prompt` + `examples` + `allowed_node_types`) | the extractor reads *this* framework → a framework-accurate graph (where tools/prompts/egress/data live) |
| Weakness graph | **behavioral** (`threat_rules_path`) + **mappings** | the rule engine evaluates the pack's `.rule.yaml` over the graph → findings **born resolved** to `weakness_id` + controls |
| Test / red-team | **behavioral** + `testgen.patterns` | the attacker aims at the paths the rules flagged |
| Remediate | **mappings** (`weakness_id → controls`) | drives the policy bundle |

**Call flow:** `check-planner` profile → `rules.fetch(profile)` (or local load) → scan with the pack's
semgrep + build the graph through its `system_prompt`/`examples` →
`ThreatRuleEngine.from_records(fetched).evaluate_graph(graph)` → findings → the usual remediate/report.
The heavy work (semgrep, graph build, CEL eval) is client-side; only the pack *content* is served.

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

- check-planner — profiles the target, resolves the vendor packs, and emits the standard-checks plan
- engagement — opens/checkpoints the long-lived engagement (context + history) around the run
- knowledge-recall, memory-capture — the common-knowledge + memory bookends (recall first, capture last)
- packs / `rules.fetch` (MCP) — framework/provider/runtime/harness rule packs; evaluated by the
  threat-rule engine over the built graph
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
