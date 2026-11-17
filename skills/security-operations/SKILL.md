---
name: security-operations
description: Orchestrates run/build-time agent-security operations — triage an alert or finding, investigate, hunt, respond to an incident, report, and evaluate — against a live or recorded AI agent, without a hosted backend. Use when a SOC analyst, incident responder, or threat hunter asks to triage, investigate, hunt, contain, respond to, or report on an agent-security event (a runtime alert, a canary hit, a scan finding, a suspected incident).
---

# Security Operations (ops orchestrator)

> Realized as the **`soc-triage`**, **`incident-response`**, and **`threat-hunt`** playbooks
> (`playbooks/*.yaml`), run by `playbook-runner`. This skill is the named entrypoint; each pipeline
> below is a playbook's composition **as data**, so an org customizes an op by editing YAML — not this
> skill.

Run agent-security **operations** locally, composing the AsterGuard runbook skills. Where
`security-engineer` is the pre-release AppSec orchestrator (find + test + rank + remediate a target
before ship), this is its run/build-time twin: **triage → investigate → hunt → respond → report →
evaluate** an agent that is already deployed or being exercised. The target is a **live agent
endpoint**, a **runtime alert / canary hit**, or a **scan finding**; the deliverable is a dispositioned,
contained, reported, and graded engagement — backed by the same security graph + event stream the
AsterGuard platform reads.

## When to Activate

- A SOC analyst asks to "triage / investigate / hunt / respond to / report on" an agent-security event.
- A runtime `security.*` alert, a `canary.verify → fired` egress hit, or a scan finding needs a
  disposition and (if real) a response.
- The request is for local or offline ops (no AsterGuard server, air-gapped, on a client box).
- Any time two or more ops runbooks below need to run in sequence against one engagement.

## Core Concepts

An operation is a staged, resumable pipeline over a **long-lived engagement**, not a one-shot scan.
Each stage is its own runbook skill; each reads/writes `./.asterguard/` and appends typed events to the
engagement's `events.jsonl` so stages are cacheable, resumable, auditable — and **gradable** (the
`evals` skill replays the event stream). Build to the shared graph/event schema so nothing is
re-derived to push to the platform later. The harness model does the analysis, judgment, and
containment authoring; the gateway only grounds, meters, verifies (canary/audit), and serves pack
content. There is no "the server decides".

## The pipeline

1. **Recall + open.** `knowledge-recall` pulls the common knowledge + prior memory for this agent/area
   (approved patterns, past incidents/findings/decisions/waivers) so the op starts informed; then
   `engagement.open(target)` loads the folded context + history. Connected: ensure the org's ARS token
   via `ars-token` so metered calls are authorized.
2. **Triage.** The matching triage runbook (`triage-agent-alert`, `triage-agent-finding`,
   `suspicious-tool-call-triage`, `malicious-dependency-triage`, `cloud-agent-vuln-triage`,
   `endpoint-agent-triage-isolation`) grades the event: `enrich-indicator` grounds the indicator,
   `risk.score` gives a first-pass read, and a `verdict` event routes it — **escalate / investigate /
   hunt / close**.
3. **Investigate.** On escalation, `investigate-agent-incident` (with `deep-dive-indicator-analysis`,
   `agent-timeline-analysis`, `correlate-finding-groups`) reconstructs what the agent did and scopes the
   blast radius from the runtime audit + the authority graph.
4. **Hunt.** Proactively or to widen scope, a `hunt-*` runbook (over-privilege, prompt-injection
   exposure, exfil paths, credential-access TTP, tool-abuse/lateral, campaign/APT) sweeps the graph +
   recorded events for the same pattern elsewhere — untrusted-input→privileged-action, confidential→
   egress, excess authority.
5. **Respond (human-gated).** For a confirmed incident, the right `irp-*` runbook (prompt-injection,
   agent-credential-compromise, tool-abuse-RCE, data-exfil-via-agent, model-supply-chain) drives PICERL:
   `contain-indicator` → `confirm-action` → `remediation` cuts the abused authority as least-privilege
   policy-as-code; a fresh `canary` run verifies the path now **holds**. Every state-changing action is
   `confirm-action`-gated and recorded as a `decision` event with its `audit_id`.
6. **Harden.** `detection-as-code-agent-rules` ships a `.rule.yaml` so the pattern is caught next time;
   `post-incident-review` captures lessons.
7. **Report.** `agent-alert-report` / `agent-incident-report` / `detection-report` folds the engagement
   trace into the deliverable (naming the runbook used at the top) — an HTML Artifact or
   `./.asterguard/reports/*.md`.
8. **Evaluate.** `evals` grades the run on four axes (trajectory, schema, rubric 0–100, benchmark)
   against the runbook's dataset case — so the op is defensible and regressions are caught.
9. **Checkpoint.** `record-in-engagement` the typed events; `engagement.checkpoint`; `memory-capture`
   the decisions/findings/fixes/waivers (with the *why*) to team memory. The loop closes.

## Pack enrichment — read the agent through its vendor packs

Every stage is grounded in the **packs** for the agent's detected vendors (agent-framework / provider /
runtime / harness), so a LangChain agent is triaged and hunted *as LangChain*. `check-planner` profiles
the target and resolves the packs — **connected** via `rules.fetch(profile)` (the MCP serves rule
content; the client evaluates locally), or **offline** from disk. Each op pulls the facet it needs:

| Stage | Pack facet | How it enriches the op |
|---|---|---|
| Recall + open | the pack set | `rules.fetch(profile)` → which lanes/rules/frameworks apply to this agent |
| Triage / hunt | **behavioral** (`threat_rules_path`) + **mappings** | the `ThreatRuleEngine` evaluates the pack's `.rule.yaml` over the graph/events → findings **born resolved** to `weakness_id` + controls |
| Investigate | **how-to-read** (`system_prompt`/`examples`/`allowed_node_types`) | the timeline/graph is reconstructed in *this* framework's terms (where tools/prompts/egress/data live) |
| Respond | **mappings** (`weakness_id → controls`) | drives the least-privilege policy bundle |
| Harden | **behavioral** + `testgen.patterns` | the new detection rule aims at the path the incident proved |

## Practical Guidance

- **Entry-point branch (low freedom):** `alert`/`canary_hit` → `soc-triage`; `confirmed incident` →
  `incident-response`; `hypothesis`/`proactive` → `threat-hunt`. A triage that escalates hands off to
  the IRP playbook; a hunt that finds a live threat opens an incident.
- **Human-in-the-loop (dual-use discipline):** every containment/state-changing action routes through
  `confirm-action` first and is a `decision` event — never auto-contain. Offline, containment is
  advisory (policy emitted, not applied); note it pending.
- **Fail-open grounding (medium freedom):** a degraded grounding/metering lane degrades that lane, never
  the op; set the run `Partial` and note it.
- **One engagement, many events:** every stage appends to the same `events.jsonl`; never fork a second
  engagement for the same target. Keep each stage's output in `./.asterguard/<stage>.json`, reference by
  path, not by inlining payloads.
- **Not done until graded:** an op (and the runbook it exercised) is complete only when `evals` has a
  dataset case and a scorecard for it.

## Integration

- check-planner — profiles the agent, resolves the vendor packs, emits the plan
- knowledge-recall, memory-capture — the knowledge + memory bookends (recall first, capture last)
- engagement — opens/checkpoints the long-lived engagement (context + history) around the op
- enrich-indicator, record-in-engagement, confirm-action, contain-indicator, remediation — the common steps
- triage-agent-alert / triage-agent-finding / suspicious-tool-call-triage / … — triage runbooks
- investigate-agent-incident, deep-dive-indicator-analysis, agent-timeline-analysis, correlate-finding-groups — investigation
- the `hunt-*` runbooks — hunting
- the `irp-*` runbooks + post-incident-review — response (PICERL)
- detection-as-code-agent-rules — harden (ship the detection)
- agent-incident-report / agent-alert-report / detection-report — output
- evals — grade the run (trajectory / schema / rubric / benchmark); security-judge / judge — the evaluators it reuses
- playbook-runner — executes the three ops playbooks that realize this orchestrator

## References

- [Operational runbooks SSOT](../../docs/RUNBOOKS.md)
- [Runbook guidelines](../../docs/RUNBOOK_GUIDELINES.md)
- Playbooks: `../../playbooks/soc-triage.yaml`, `../../playbooks/incident-response.yaml`,
  `../../playbooks/threat-hunt.yaml`
